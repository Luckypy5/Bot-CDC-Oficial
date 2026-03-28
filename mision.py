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

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix='!', intents=intents)

turnos_activos = {}

# --- CATÁLOGO DE MISIONES ---
misiones_semanales = {
    0: {"t": "🛂 Operación: 'Papeles en Regla'", "d": "Fiscalización técnica en Peajes o Accesos.", "r": "Solicitar documentos y verificar patente.", "e": "Foto frente al vehículo."},
    1: {"t": "🏢 Operación: 'Identidad de Bloque'", "d": "Saturación en callejones o bloques de LS.", "r": "Oficiales a pie. Consulta de antecedentes.", "e": "Foto del registro en el bloque."},
    2: {"t": "🏍️ Operación: 'Binomio Los Santos'", "d": "Patrullaje motorizado (Sanchez o BMW).", "r": "Vigilancia en ciudad o cerros.", "e": "Foto de las motos juntas."},
    3: {"t": "🚛 Operación: 'Ruta Segura'", "d": "Escolta oficial a Camioneros.", "r": "Ubicar camionero y abrir paso con balizas.", "e": "Foto de la patrulla escoltando."},
    4: {"t": "🦅 Operación: 'Día de Especialista'", "d": "Libre Disposición (GOPE, Prefectura, SIP).", "r": "Ramas especiales en servicio.", "e": "Foto con uniforme o vehículo especial."}
}

# --- SISTEMA DE ASISTENCIA ---
class MenuAsistencia(discord.ui.View):
    def _init_(self):
        super()._init_(timeout=None)

    @discord.ui.button(label="Entrar Servicio (10-39)", style=discord.ButtonStyle.green, custom_id="btn_entrar_v2")
    async def entrar_servicio(self, interaction: discord.Interaction, button: discord.ui.Button):
        user_id = interaction.user.id
        if user_id in turnos_activos:
            await interaction.response.send_message("⚠️ Ya tienes un turno activo.", ephemeral=True)
        else:
            turnos_activos[user_id] = datetime.datetime.now(ZONA_HORARIA)
            await interaction.response.send_message(f"🟢 *10-39* registrado correctamente.", ephemeral=True)

    @discord.ui.button(label="Salir Servicio (10-10)", style=discord.ButtonStyle.red, custom_id="btn_salir_v2")
    async def salir_servicio(self, interaction: discord.Interaction, button: discord.ui.Button):
        user_id = interaction.user.id
        if user_id not in turnos_activos:
            await interaction.response.send_message("❌ No has iniciado turno.", ephemeral=True)
        else:
            inicio = turnos_activos.pop(user_id)
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

            await interaction.response.send_message(f"🔴 *10-10* registrado. Tiempo enviado a Jefatura.", ephemeral=True)

@bot.command()
@commands.has_permissions(administrator=True)
async def panel(ctx):
    embed = discord.Embed(title="🚓 CONTROL DE ASISTENCIA CDC", description="Presiona los botones para marcar tu estado.", color=discord.Color.green())
    await ctx.send(embed=embed, view=MenuAsistencia())

@bot.event
async def on_ready():
    print(f'✅ Sistema CDC Online')
    bot.add_view(MenuAsistencia())

bot.run(TOKEN)
