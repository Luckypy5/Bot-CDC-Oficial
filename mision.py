import discord
from discord.ext import commands, tasks
import datetime
import pytz
import random
import os

# --- CONFIGURACIÓN ---
TOKEN = os.getenv('DISCORD_TOKEN')
ID_CANAL_MISIONES = 1478505943711875112
ID_CANAL_PRIVADO = 1487316210336137287 
ZONA_HORARIA = pytz.timezone('America/Santiago')

# --- CATÁLOGO DE MISIONES ---
misiones_semanales = {
    0: {"t": "🛂 LUNES: 'Papeles en Regla'", "d": "Fiscalización técnica en Peajes."},
    1: {"t": "🏢 MARTES: 'Identidad de Bloque'", "d": "Saturación en callejones de LS."},
    2: {"t": "🏍️ MIÉRCOLES: 'Binomio Los Santos'", "d": "Patrullaje motorizado."},
    3: {"t": "🚛 JUEVES: 'Ruta Segura'", "d": "Escolta oficial a Camioneros."},
    4: {"t": "🦅 VIERNES: 'Día de Especialista'", "d": "Libre Disposición."},
    5: {"t": "🚔 SÁBADO: 'Saturación Central'", "d": "Controles masivos en Plaza Central."},
    6: {"t": "🌄 DOMINGO: 'Vigilancia Rural'", "d": "Patrullaje en Paleto o Sandy Shores."}
}

# --- VISTA PERSISTENTE ---
class MenuAsistencia(discord.ui.View):
    def _init_(self):
        super()._init_(timeout=None)

    @discord.ui.button(label="Entrar Servicio (10-39)", style=discord.ButtonStyle.green, custom_id="v7_entrar")
    async def entrar(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id in turnos_activos:
            return await interaction.response.send_message("⚠️ Ya tienes un turno activo.", ephemeral=True)
        turnos_activos[interaction.user.id] = datetime.datetime.now(ZONA_HORARIA)
        await interaction.response.send_message("🟢 *10-39* registrado.", ephemeral=True)

    @discord.ui.button(label="Salir Servicio (10-10)", style=discord.ButtonStyle.red, custom_id="v7_salir")
    async def salir(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id not in turnos_activos:
            return await interaction.response.send_message("❌ No has iniciado turno.", ephemeral=True)
        
        inicio = turnos_activos.pop(interaction.user.id)
        fin = datetime.datetime.now(ZONA_HORARIA)
        dif = fin - inicio
        horas, segundos = divmod(dif.total_seconds(), 3600)
        minutos = (segundos // 60)

        canal = bot.get_channel(ID_CANAL_PRIVADO)
        if canal:
            embed = discord.Embed(title="📄 REPORTE DE PATRULLAJE", color=discord.Color.green())
            embed.add_field(name="Oficial", value=interaction.user.display_name, inline=True)
            embed.add_field(name="Tiempo", value=f"{int(horas)}h {int(minutos)}m", inline=True)
            await canal.send(embed=embed)
        await interaction.response.send_message("🔴 *10-10* registrado.", ephemeral=True)

# --- INICIALIZACIÓN DEL BOT ---
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix='!', intents=intents)
turnos_activos = {}

# --- SETUP PERSISTENTE (CRÍTICO) ---
@bot.event
async def setup_hook():
    # Esto registra los botones ANTES de que el bot se conecte del todo
    bot.add_view(MenuAsistencia())

@bot.event
async def on_ready():
    print(f'✅ Bot listo como: {bot.user}')
    if not enviar_mision.is_running():
        enviar_mision.start()

# --- TAREA DE MISIONES ---
@tasks.loop(time=datetime.time(hour=0, minute=0, tzinfo=ZONA_HORARIA))
async def enviar_mision():
    canal = bot.get_channel(ID_CANAL_MISIONES)
    if canal:
        dia = datetime.datetime.now(ZONA_HORARIA).weekday()
        m = misiones_semanales.get(dia)
        embed = discord.Embed(title=f"📅 {m['t']}", description=m['d'], color=discord.Color.blue())
        await canal.send(embed=embed)

@bot.command()
@commands.has_permissions(administrator=True)
async def panel(ctx):
    await ctx.send(content="🚓 *ASISTENCIA CDC*", view=MenuAsistencia())

bot.run(TOKEN)
