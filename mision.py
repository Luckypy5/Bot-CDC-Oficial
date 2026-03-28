import discord
from discord.ext import commands, tasks
import datetime
import pytz
import os

# --- CONFIGURACIÓN ---
TOKEN = os.getenv('DISCORD_TOKEN')
ID_CANAL_MISIONES = 1478505943711875112
ID_CANAL_PRIVADO = 1487316210336137287 
ZONA_HORARIA = pytz.timezone('America/Santiago')

# --- BOT ---
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix='!', intents=intents)
turnos_activos = {}

# --- VISTA PERSISTENTE ---
class MenuAsistencia(discord.ui.View):
    def _init_(self):
        super()._init_(timeout=None)

    @discord.ui.button(label="Entrar Servicio (10-39)", style=discord.ButtonStyle.green, custom_id="cdc_vFINAL_entrar")
    async def entrar(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id in turnos_activos:
            return await interaction.response.send_message("⚠️ Ya tienes un turno activo.", ephemeral=True)
        turnos_activos[interaction.user.id] = datetime.datetime.now(ZONA_HORARIA)
        await interaction.response.send_message("🟢 *10-39* registrado.", ephemeral=True)

    @discord.ui.button(label="Salir Servicio (10-10)", style=discord.ButtonStyle.red, custom_id="cdc_vFINAL_salir")
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
            embed.add_field(name="Oficial", value=interaction.user.display_name, inline=False)
            embed.add_field(name="Tiempo Total", value=f"{int(horas)}h {int(minutos)}m", inline=False)
            await canal.send(embed=embed)
        await interaction.response.send_message("🔴 *10-10* registrado.", ephemeral=True)

# --- EVENTOS ---
@bot.event
async def on_ready():
    # Esto es lo que hace que los botones funcionen tras un reinicio
    bot.add_view(MenuAsistencia())
    print(f'✅ Bot CDC Online: {bot.user}')

@bot.command()
@commands.has_permissions(administrator=True)
async def panel(ctx):
    embed = discord.Embed(title="🚓 CONTROL DE ASISTENCIA CDC", description="Marca tu estado de servicio aquí.", color=discord.Color.blue())
    await ctx.send(embed=embed, view=MenuAsistencia())

bot.run(TOKEN)


