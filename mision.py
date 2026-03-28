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

# --- CLASE DE ASISTENCIA PERSISTENTE ---
class MenuAsistencia(discord.ui.View):
    def _init_(self):
        # El timeout=None hace que los botones no caduquen NUNCA
        super()._init_(timeout=None)

    # El custom_id debe ser ÚNICO y no cambiar nunca
    @discord.ui.button(label="Entrar Servicio (10-39)", style=discord.ButtonStyle.green, custom_id="cdc_btn_entrar_v3")
    async def entrar_servicio(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id in turnos_activos:
            await interaction.response.send_message("⚠️ Ya tienes un turno activo.", ephemeral=True)
        else:
            turnos_activos[interaction.user.id] = datetime.datetime.now(ZONA_HORARIA)
            await interaction.response.send_message(f"🟢 *10-39* registrado correctamente.", ephemeral=True)

    @discord.ui.button(label="Salir Servicio (10-10)", style=discord.ButtonStyle.red, custom_id="cdc_btn_salir_v3")
    async def salir_servicio(self, interaction: discord.Interaction, button: discord.ui.Button):
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

            await interaction.response.send_message(f"🔴 *10-10* registrado. Reporte enviado.", ephemeral=True)

# --- CONFIGURACIÓN DEL BOT ---
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix='!', intents=intents)

# NOTA: turnos_activos se limpia si el bot se apaga. 
# Si quieres que el patrullaje sobreviva a reinicios, necesitaremos una DB.
turnos_activos = {}

@bot.event
async def on_ready():
    # REGISTRO DE VISTA PERSISTENTE
    # Esto es lo que evita el error rojo que viste en el log
    bot.add_view(MenuAsistencia())
    print(f'✅ Sistema CDC Online y Persistente')

@bot.command()
@commands.has_permissions(administrator=True)
async def panel(ctx):
    embed = discord.Embed(
        title="🚓 CONTROL DE ASISTENCIA CDC", 
        description="Presiona los botones para marcar tu estado.", 
        color=discord.Color.green()
    )
    await ctx.send(embed=embed, view=MenuAsistencia())

bot.run(TOKEN)
