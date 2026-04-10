import discord
from discord.ext import commands
import datetime
import pytz
import os
from flask import Flask
from threading import Thread

# --- SERVIDOR PARA MANTENER EL BOT VIVO (OBLIGATORIO PARA RENDER GRATIS) ---
app = Flask('')

@app.route('/')
def home():
    return "Servicio de Carabineros Online"

def run():
    app.run(host='0.0.0.0', port=10000)

def keep_alive():
    t = Thread(target=run)
    t.start()

# --- CONFIGURACIÓN ---
TOKEN = os.getenv('DISCORD_TOKEN')
ID_CANAL_PRIVADO = 1487316210336137287 
ZONA_HORARIA = pytz.timezone('America/Santiago')

intents = discord.Intents.default()
intents.message_content = True 
bot = commands.Bot(command_prefix='!', intents=intents)
turnos_activos = {}

@bot.event
async def on_ready():
    print(f'✅ Sistema Carabineros de Chile Online | Sin misiones diarias.')

# --- COMANDOS DE ASISTENCIA ---

@bot.command(name="inicio")
async def inicio(ctx):
    try: await ctx.message.delete()
    except: pass
    if ctx.author.id in turnos_activos:
        return await ctx.send(f"⚠️ {ctx.author.mention}, ya constas en servicio activo.", delete_after=5)
    
    ahora = datetime.datetime.now(ZONA_HORARIA)
    turnos_activos[ctx.author.id] = ahora
    
    embed = discord.Embed(
        title="🟢 INICIO DE SERVICIO - CARABINEROS DE CHILE", 
        description=f"El oficial **{ctx.author.mention}** ha iniciado funciones.", 
        color=discord.Color.from_rgb(0, 104, 71)
    )
    embed.add_field(name="🕒 10-39", value=ahora.strftime('%H:%M:%S'), inline=True)
    embed.set_footer(text="Orden y Patria")
    await ctx.send(embed=embed)

@bot.command(name="termino")
async def termino(ctx):
    try: await ctx.message.delete()
    except: pass
    if ctx.author.id not in turnos_activos:
        return await ctx.send(f"❌ No registras un inicio de servicio previo.", delete_after=5)
    
    inicio_t = turnos_activos.pop(ctx.author.id)
    ahora = datetime.datetime.now(ZONA_HORARIA)
    duracion = ahora - inicio_t
    
    h, r = divmod(int(duracion.total_seconds()), 3600)
    m, _ = divmod(r, 60)
    
    await ctx.send(embed=discord.Embed(
        title="🔴 TÉRMINO DE SERVICIO", 
        description=f"El oficial **{ctx.author.mention}** finaliza servicio (10-10).", 
        color=discord.Color.from_rgb(180, 0, 0)
    ))

    canal = bot.get_channel(ID_CANAL_PRIVADO)
    if canal:
        reporte = discord.Embed(title="📄 BITÁCORA OFICIAL DE GUARDIA", color=discord.Color.dark_green())
        reporte.add_field(name="👮 Oficial", value=ctx.author.mention, inline=False)
        reporte.add_field(name="⏳ Jornada", value=f"**{h}h {m}m**", inline=True)
        reporte.set_footer(text=f"Fecha: {ahora.strftime('%d/%m/%Y')} | Archivo Jefatura")
        await canal.send(embed=reporte)

@bot.command(name="activos")
async def activos(ctx):
    try: await ctx.message.delete()
    except: pass
    if not turnos_activos:
        return await ctx.send("🚫 No hay unidades en frecuencia radial.", delete_after=10)
    
    lista = "\n".join([f"• <@{uid}>" for uid in turnos_activos.keys()])
    embed = discord.Embed(title="🚔 UNIDADES EN 10-39", description=lista, color=discord.Color.gold())
    await ctx.send(embed=embed, delete_after=45)

@bot.command(name="parar")
@commands.has_permissions(administrator=True)
async def parar(ctx, miembro: discord.Member):
    try: await ctx.message.delete()
    except: pass
    if miembro.id in turnos_activos:
        turnos_activos.pop(miembro.id)
        await ctx.send(embed=discord.Embed(
            title="⚠️ SANCIÓN ADMINISTRATIVA", 
            description=f"Cierre forzado de servicio para {miembro.mention}.\n**Ordenado por:** {ctx.author.mention}", 
            color=discord.Color.orange()
        ))

# --- LANZAMIENTO ---
if __name__ == "__main__":
    keep_alive()
    bot.run(TOKEN)
