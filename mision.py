import discord
from discord.ext import commands
import datetime
import pytz
import os

# --- CONFIGURACIÓN ---
TOKEN = os.getenv('DISCORD_TOKEN')
ID_CANAL_PRIVADO = 1487316210336137287 
ZONA_HORARIA = pytz.timezone('America/Santiago')

# --- INICIALIZACIÓN ---
intents = discord.Intents.default()
intents.message_content = True 
bot = commands.Bot(command_prefix='!', intents=intents)

# Memoria de turnos
turnos_activos = {}

@bot.event
async def on_ready():
    print(f'✅ Sistema CDC Online | !inicio, !termino, !activos')

# --- COMANDO INICIO ---
@bot.command(name="inicio")
async def inicio_servicio(ctx):
    try: await ctx.message.delete()
    except: pass

    if ctx.author.id in turnos_activos:
        return await ctx.send(f"⚠️ **{ctx.author.display_name}**, ya tienes un turno activo.", delete_after=10)

    turnos_activos[ctx.author.id] = datetime.datetime.now(ZONA_HORARIA)
    embed = discord.Embed(
        description=f"🟢 **10-39** | **{ctx.author.display_name}** ha iniciado su servicio.",
        color=discord.Color.green()
    )
    await ctx.send(embed=embed, delete_after=15)

# --- COMANDO TERMINO ---
@bot.command(name="termino")
async def termino_servicio(ctx):
    try: await ctx.message.delete()
    except: pass

    if ctx.author.id not in turnos_activos:
        return await ctx.send(f"❌ No tienes un turno activo.", delete_after=10)

    # Procesar salida
    inicio = turnos_activos.pop(ctx.author.id)
    ahora = datetime.datetime.now(ZONA_HORARIA)
    duracion = ahora - inicio
    horas, resto = divmod(int(duracion.total_seconds()), 3600)
    minutos, _ = divmod(resto, 60)

    await ctx.send(f"🔴 **10-10** | **{ctx.author.display_name}** finalizó servicio.", delete_after=15)

    # Reporte a Jefatura
    canal = bot.get_channel(ID_CANAL_PRIVADO)
    if canal:
        reporte = discord.Embed(title="📄 REGISTRO DE JORNADA", color=discord.Color.blue())
        reporte.add_field(name="👮 Oficial", value=ctx.author.mention, inline=True)
        reporte.add_field(name="⏳ Tiempo", value=f"**{horas}h {minutos}m**", inline=True)
        reporte.set_footer(text=f"Fecha: {ahora.strftime('%d/%m/%Y')}")
        await canal.send(embed=reporte)

# --- COMANDO PARA VER ACTIVOS ---
@bot.command(name="activos")
async def activos(ctx):
    try: await ctx.message.delete()
    except: pass

    if not turnos_activos:
        return await ctx.send("🚫 No hay oficiales en servicio.", delete_after=10)
    
    lista = "\n".join([f"• <@{uid}> (Inició: {t.strftime('%H:%M')})" for uid, t in turnos_activos.items()])
    embed = discord.Embed(title="🚔 Oficiales en Servicio", description=lista, color=discord.Color.gold())
    await ctx.send(embed=embed, delete_after=30)

# --- COMANDO DE JEFATURA: FORZAR CIERRE (!parar @usuario) ---
@bot.command(name="parar")
@commands.has_permissions(administrator=True) # SOLO ADMINS
async def parar_otro(ctx, miembro: discord.Member):
    try: await ctx.message.delete()
    except: pass

    if miembro.id not in turnos_activos:
        return await ctx.send(f"El oficial {miembro.display_name} no está en servicio.", delete_after=10)

    # Cerrar turno a la fuerza
    inicio = turnos_activos.pop(miembro.id)
    ahora = datetime.datetime.now(ZONA_HORARIA)
    duracion = ahora - inicio
    horas, resto = divmod(int(duracion.total_seconds()), 3600)
    minutos, _ = divmod(resto, 60)

    # Avisar en el canal
    await ctx.send(f"🛑 **CIERRE FORZADO** | El turno de {miembro.mention} ha sido finalizado por Jefatura.", delete_after=20)

    # Reporte especial a Jefatura
    canal = bot.get_channel(ID_CANAL_PRIVADO)
    if canal:
        reporte = discord.Embed(title="⚠️ CIERRE DE TURNO FORZADO", color=discord.Color.orange())
        reporte.add_field(name="👮 Oficial", value=miembro.mention, inline=True)
        reporte.add_field(name="🛡️ Cerrado por", value=ctx.author.mention, inline=True)
        reporte.add_field(name="⏳ Tiempo acumulado", value=f"{horas}h {minutos}m", inline=False)
        reporte.set_footer(text="Acción Administrativa")
        await canal.send(embed=reporte)

# Error si alguien sin permiso intenta usar !parar
@parar_otro.error
async def parar_error(ctx, error):
    if isinstance(error, commands.MissingPermissions):
        await ctx.send("🚫 No tienes rango de Jefatura para usar este comando.", delete_after=5)

bot.run(TOKEN)
