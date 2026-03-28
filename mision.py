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

# --- MISIONES INSTITUCIONALES ---
misiones_dict = {
    0: "LUNES: Fiscalización técnica en Peajes. Revisar documentación y patentes.",
    1: "MARTES: Saturación en callejones de LS. Control de identidad preventivo.",
    2: "MIÉRCOLES: Patrullaje motorizado en binomios por el sector céntrico.",
    3: "JUEVES: Escolta oficial a camiones de carga en Ruta 5.",
    4: "VIERNES: Operativo especial (Ramas especializadas GOPE/SIP).",
    5: "SÁBADO: Control masivo de baúles y vehículos en Plaza Central.",
    6: "DOMINGO: Vigilancia rural en sectores alejados y estaciones de servicio."
}

# --- INICIALIZACIÓN ---
intents = discord.Intents.default()
intents.message_content = True 
bot = commands.Bot(command_prefix='!', intents=intents)
turnos_activos = {}

@bot.event
async def on_ready():
    print(f'✅ Sistema CDC Final Online | !inicio, !termino, !activos, !parar, !mision')
    if not enviar_mision_diaria.is_running():
        enviar_mision_diaria.start()

# --- TAREA AUTOMÁTICA MISIONES (00:00) ---
@tasks.loop(time=datetime.time(hour=0, minute=0, tzinfo=ZONA_HORARIA))
async def enviar_mision_diaria():
    canal = bot.get_channel(ID_CANAL_MISIONES)
    if canal:
        dia = datetime.datetime.now(ZONA_HORARIA).weekday()
        embed = discord.Embed(title="📅 HOJA DE RUTA DIARIA", description=f"**Misión:** {misiones_dict[dia]}", color=discord.Color.blue())
        await canal.send(embed=embed)

# --- COMANDO MISIÓN MANUAL ---
@bot.command(name="mision")
async def mision(ctx):
    try: await ctx.message.delete()
    except: pass
    dia = datetime.datetime.now(ZONA_HORARIA).weekday()
    await ctx.send(f"📋 **Orden de servicio actual:** {misiones_dict[dia]}", delete_after=60)

# --- COMANDO INICIO (10-39) ---
@bot.command(name="inicio")
async def inicio(ctx):
    try: await ctx.message.delete()
    except: pass
    if ctx.author.id in turnos_activos:
        return await ctx.send(f"⚠️ Oficial, su servicio ya consta en bitácora.", delete_after=10)
    
    ahora = datetime.datetime.now(ZONA_HORARIA)
    turnos_activos[ctx.author.id] = ahora
    embed = discord.Embed(title="🟢 INICIO DE SERVICIO - CDC", description=f"El oficial **{ctx.author.mention}** ha iniciado funciones.", color=discord.Color.from_rgb(0, 104, 71))
    embed.add_field(name="🕒 10-39", value=f"Hora: {ahora.strftime('%H:%M:%S')}")
    await ctx.send(embed=embed)

# --- COMANDO TERMINO (10-10) ---
@bot.command(name="termino")
async def termino(ctx):
    try: await ctx.message.delete()
    except: pass
    if ctx.author.id not in turnos_activos:
        return await ctx.send(f"❌ No se registra un inicio de servicio previo.", delete_after=10)

    inicio_t = turnos_activos.pop(ctx.author.id)
    ahora = datetime.datetime.now(ZONA_HORARIA)
    duracion = ahora - inicio_t
    h, r = divmod(int(duracion.total_seconds()), 3600)
    m, _ = divmod(r, 60)

    await ctx.send(embed=discord.Embed(title="🔴 TÉRMINO DE SERVICIO - CDC", description=f"El oficial **{ctx.author.mention}** finaliza funciones.", color=discord.Color.from_rgb(180, 0, 0)))

    canal = bot.get_channel(ID_CANAL_PRIVADO)
    if canal:
        reporte = discord.Embed(title="📄 BITÁCORA OFICIAL DE GUARDIA", color=discord.Color.dark_green())
        reporte.add_field(name="👮 Oficial", value=ctx.author.mention, inline=False)
        reporte.add_field(name="📥 Entrada", value=inicio_t.strftime('%H:%M:%S'), inline=True)
        reporte.add_field(name="📤 Salida", value=ahora.strftime('%H:%M:%S'), inline=True)
        reporte.add_field(name="⏳ Jornada", value=f"{h}h {m}m", inline=True)
        await canal.send(embed=reporte)

# --- COMANDO ACTIVOS ---
@bot.command(name="activos")
async def activos(ctx):
    try: await ctx.message.delete()
    except: pass
    if not turnos_activos:
        return await ctx.send("🚫 No hay unidades en frecuencia.", delete_after=10)
    lista = "\n".join([f"• <@{uid}> (Desde: {t.strftime('%H:%M')})" for uid, t in turnos_activos.items()])
    await ctx.send(embed=discord.Embed(title="🚔 UNIDADES EN 10-39", description=lista, color=discord.Color.gold()), delete_after=45)

# --- COMANDO PARAR (Abuso de tiempo) ---
@bot.command(name="parar")
@commands.has_permissions(administrator=True)
async def parar(ctx, miembro: discord.Member):
    try: await ctx.message.delete()
    except: pass
    if miembro.id in turnos_activos:
        inicio_t = turnos_activos.pop(miembro.id)
        ahora = datetime.datetime.now(ZONA_HORARIA)
        duracion = ahora - inicio_t
        h, r = divmod(int(duracion.total_seconds()), 3600)
        m, _ = divmod(r, 60)
        
        await ctx.send(f"🛑 **CIERRE FORZADO** | El turno de {miembro.mention} fue finalizado por Jefatura.", delete_after=15)
        
        canal = bot.get_channel(ID_CANAL_PRIVADO)
        if canal:
            reporte = discord.Embed(title="⚠️ CIERRE DE TURNO FORZADO", color=discord.Color.orange())
            reporte.add_field(name="👮 Oficial", value=miembro.mention)
            reporte.add_field(name="🛡️ Por", value=ctx.author.mention)
            reporte.add_field(name="⏳ Tiempo", value=f"{h}h {m}m")
            await canal.send(embed=reporte)

bot.run(TOKEN)
