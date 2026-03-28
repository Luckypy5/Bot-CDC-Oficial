import discord
from discord.ext import commands, tasks
import datetime
import pytz
import random
import os

# --- CONFIGURACIÓN DE IDS ---
TOKEN = os.getenv('DISCORD_TOKEN')
ID_CANAL_MISIONES = 1478505943711875112
ID_CANAL_PRIVADO = 1487316210336137287 
ZONA_HORARIA = pytz.timezone('America/Santiago')

# --- CONFIGURACIÓN DEL BOT ---
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix='!', intents=intents)

turnos_activos = {}

# --- CATÁLOGO DE MISIONES (COLOR VERDE) ---
misiones_semanales = {
    0: {"t": "🛂 Operación: 'Papeles en Regla'", "d": "Fiscalización técnica en Peajes o Accesos.", "r": "Solicitar documentos y verificar patente. Si no hay: Multa Tabla.", "e": "Foto frente al vehículo."},
    1: {"t": "🏢 Operación: 'Identidad de Bloque'", "d": "Saturación en callejones o bloques de LS.", "r": "Oficiales a pie. Consulta de antecedentes o búsqueda de ilícitos.", "e": "Foto del registro en el bloque."},
    2: {"t": "🏍️ Operación: 'Binomio Los Santos'", "d": "Patrullaje motorizado (Sanchez o BMW).", "r": "Vigilancia en ciudad o cerros. Realizar 1 control vehicular completo.", "e": "Foto de las motos juntas."},
    3: {"t": "🚛 Operación: 'Ruta Segura'", "d": "Escolta oficial a Camioneros.", "r": "Ubicar camionero y abrir paso con balizas hasta el destino.", "e": "Foto de la patrulla escoltando al camión."},
    4: {"t": "🦅 Operación: 'Día de Especialista'", "d": "Libre Disposición.", "r": "Ramas: GOPE (Tahoe), Prefectura Aérea (Helicóptero), o Inteligencia (OS7/OS9/SIP).", "e": "Foto con uniforme o vehículo especial."}
}

# --- SISTEMA DE ASISTENCIA (BOTONES CORREGIDOS) ---
class MenuAsistencia(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="Entrar Servicio (10-39)", style=discord.ButtonStyle.green, custom_id="btn_entrar")
    async def entrar_callback(self, button: discord.ui.Button, interaction: discord.Interaction):
        if interaction.user.id in turnos_activos:
            await interaction.response.send_message("⚠️ Ya tienes un turno activo.", ephemeral=True)
        else:
            turnos_activos[interaction.user.id] = datetime.datetime.now(ZONA_HORARIA)
            await interaction.response.send_message(f"🟢 **10-39** registrado correctamente.", ephemeral=True)

    @discord.ui.button(label="Salir Servicio (10-10)", style=discord.ButtonStyle.red, custom_id="btn_salir")
    async def salir_callback(self, button: discord.ui.Button, interaction: discord.Interaction):
        if interaction.user.id not in turnos_activos:
            await interaction.response.send_message("❌ No has iniciado turno.", ephemeral=True)
        else:
            inicio = turnos_activos.pop(interaction.user.id)
            fin = datetime.datetime.now(ZONA_HORARIA)
            dif = fin - inicio
            horas, segundos = divmod(dif.total_seconds(), 3600)
            minutos = (segundos // 60)

            canal_privado = bot.get_channel(ID_CANAL_PRIVADO)
            if canal_privado:
                embed = discord.Embed(title="📄 REPORTE DE PATRULLAJE", color=discord.Color.green())
                embed.add_field(name="Oficial", value=interaction.user.display_name, inline=True)
                embed.add_field(name="Tiempo Total", value=f"{int(horas)}h {int(minutos)}m", inline=True)
                embed.add_field(name="Inicio", value=inicio.strftime('%H:%M'), inline=True)
                embed.add_field(name="Fin", value=fin.strftime('%H:%M'), inline=True)
                embed.set_footer(text=f"Fecha: {fin.strftime('%d/%m/%Y')}")
                await canal_privado.send(embed=embed)

            await interaction.response.send_message(f"🔴 **10-10** registrado. Tiempo enviado a Jefatura: {int(horas)}h {int(minutos)}m.", ephemeral=True)

# --- TAREA PROGRAMADA ---
@tasks.loop(time=datetime.time(hour=0, minute=0, tzinfo=ZONA_HORARIA))
async def enviar_mision_diaria():
    canal = bot.get_channel(ID_CANAL_MISIONES)
    if canal:
        dia = datetime.datetime.now(ZONA_HORARIA).weekday()
        m = misiones_semanales.get(dia, misiones_semanales[0])
        folio = random.randint(1000, 9999)
        
        embed = discord.Embed(title=f"📅 MISIÓN DIARIA: {m['t']}", color=discord.Color.green())
        embed.add_field(name="🔢 Folio", value=f"#CDC-{folio}", inline=True)
        embed.add_field(name="🎯 Objetivo", value=m['d'], inline=False)
        embed.add_field(name="🎭 Dinámica", value=m['r'], inline=False)
        embed.add_field(name="📸 Evidencia", value=m['e'], inline=False)
        embed.set_footer(text=f"CDC Operaciones | {datetime.datetime.now(ZONA_HORARIA).strftime('%d/%m/%Y')}")
        await canal.send(embed=embed)

# --- COMANDOS ---
@bot.command()
@commands.has_permissions(administrator=True)
async def panel(ctx):
    embed = discord.Embed(
        title="🚓 CONTROL DE ASISTENCIA CDC", 
        description="Presiona los botones para marcar tu estado de servicio.", 
        color=discord.Color.green()
    )
    await ctx.send(embed=embed, view=MenuAsistencia())

@bot.event
async def on_ready():
    print(f'✅ Sistema CDC Online')
    bot.add_view(MenuAsistencia())
    if not enviar_mision_diaria.is_running():
        enviar_mision_diaria.start()

bot.run(TOKEN)
