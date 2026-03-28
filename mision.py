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
    0: "LUNES: 'Papeles en Regla' - Fiscalización técnica en Peajes. Revisar documentación y patentes.",
    1: "MARTES: 'Identidad de Bloque' - Saturación en callejones. Control de identidad preventivo.",
    2: "MIÉRCOLES: 'Binomio Los Santos' - Patrullaje motorizado en binomios por el sector céntrico.",
    3: "JUEVES: 'Ruta Segura' - Escolta oficial a camiones de carga en Ruta 5.",
    4: "VIERNES: 'Día de Especialista' - Operativo especial (Ramas especializadas GOPE/SIP).",
    5: "SÁBADO: 'Saturación Central' - Control masivo de baúles y vehículos en Plaza Central.",
    6: "DOMINGO: 'Vigilancia Rural' - Vigilancia en sectores alejados y estaciones de servicio."
}

# --- INICIALIZACIÓN ---
intents = discord.Intents.default()
intents.message_content = True 
bot = commands.Bot(command_prefix='!', intents=intents)
turnos_activos = {}

@bot.event
async def on_ready():
    print(f'✅ Sistema Carabineros de Chile Online | Franco, todo listo.')
    if not enviar_mision_diaria.is_running():
        enviar_mision_diaria.start()

# --- TAREA AUTOMÁTICA MISIONES (00:00) ---
@tasks.loop(time=datetime.time(hour=0, minute=0, tzinfo=ZONA_HORARIA))
async def enviar_mision_diaria():
    canal = bot.get_channel(ID_CANAL_MISIONES)
    if canal:
        try: await canal.purge(limit=10) 
        except: pass
        dia = datetime.datetime.now(ZONA_HORARIA).weekday()
        
        embed_mision = discord.Embed(title="📅 HOJA DE RUTA DIARIA - CARABINEROS DE CHILE", description=f"**Orden de Servicio:** {misiones_dict[dia]}", color=discord.Color.from_rgb(0, 104, 71))
        await canal.send(embed=embed_mision)

        embed_bono = discord.Embed(title="💰 BONO POR ACTIVIDAD SEMANAL", description="Cumplir **3 misiones semanales** otorga un bono por actividad en su liquidación.", color=discord.Color.gold())
        embed_bono.set_footer(text="Carabineros de Chile | Jefatura Administrativa")
        await canal.send(embed=embed_bono)

# --- COMANDO MISIÓN MANUAL ---
@bot.command(name="mision")
async def mision(ctx):
    try: await ctx.message.delete()
    except: pass
    dia = datetime.datetime.now(ZONA_HORARIA).weekday()
    embed = discord.Embed(title="📋 CONSULTA DE ORDEN DE SERVICIO", description=f"**Misión para hoy:** {misiones_dict[dia]}", color=discord.Color.from_rgb(0, 104, 71))
    embed.set_footer(text="Carabineros de Chile")
    await ctx.send(embed=embed, delete_after=60)

# --- COMANDO INICIO (10-39) ---
@bot.command(name="inicio")
async def inicio(ctx):
    try: await ctx.message.delete()
    except: pass
    if ctx.author.id in turnos_activos:
        return await ctx.send(f"⚠️ Oficial, su servicio ya consta en bitácora.", delete_after=10)
    
    ahora = datetime.datetime.now(ZONA_HORARIA)
    turnos_activos[ctx.author.id] = ahora
    embed = discord.Embed(
        title="🟢 INICIO DE SERVICIO - CARABINEROS DE CHILE", 
        description=f"El oficial **{ctx.author.mention}** ha iniciado sus funciones de patrullaje preventivo.", 
        color=discord.Color.from_rgb(0, 104, 71)
    )
    embed.add_field(name="⚪ Código Radial", value="**10-39**", inline=True)
    embed.add_field(name="⚪ Hora de Entrada", value=f"**{ahora.strftime('%H:%M:%S')}**", inline=True)
    embed.set_footer(text="Carabineros de Chile | Orden y Seguridad")
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

    embed_fin = discord.Embed(
        title="🔴 TÉRMINO DE SERVICIO - CARABINEROS DE CHILE", 
        description=f"El oficial **{ctx.author.mention}** ha finalizado sus funciones y se retira de la frecuencia.", 
        color=discord.Color.from_rgb(180, 0, 0)
    )
    embed_fin.add_field(name="⚪ Código Radial", value="**10-10**", inline=True)
    embed_fin.add_field(name="⏳ Tiempo de Patrullaje", value=f"**{h}h {m}m**", inline=True)
    embed_fin.set_footer(text="Carabineros de Chile | Servicio Finalizado")
    await ctx.send(embed=embed_fin)

    canal = bot.get_channel(ID_CANAL_PRIVADO)
    if canal:
        reporte = discord.Embed(title="📄 BITÁCORA OFICIAL DE GUARDIA", color=discord.Color.dark_green())
        reporte.set_thumbnail(url=ctx.author.display_avatar.url)
        reporte.add_field(name="👮 Oficial a Cargo", value=ctx.author.mention, inline=False)
        reporte.add_field(name="📥 Ingreso (10-39)", value=f"**{inicio_t.strftime('%H:%M:%S')}**", inline=True)
        reporte.add_field(name="📤 Egreso (10-10)", value=f"**{ahora.strftime('%H:%M:%S')}**", inline=True)
        reporte.add_field(name="⏳ Jornada Total", value=f"**{h}h {m}m**", inline=True)
        reporte.set_footer(text=f"Fecha: {ahora.strftime('%d/%m/%Y')} | Archivo Jefatura Carabineros de Chile")
        await canal.send(embed=reporte)

# --- COMANDO ACTIVOS ---
@bot.command(name="activos")
async def activos(ctx):
    try: await ctx.message.delete()
    except: pass
    if not turnos_activos:
        return await ctx.send("🚫 No se registran unidades en frecuencia.", delete_after=10)
    lista = "\n".join([f"• <@{uid}> (Desde las {t.strftime('%H:%M')})" for uid, t in turnos_activos.items()])
    embed = discord.Embed(title="🚔 UNIDADES EN FRECUENCIA (10-39)", description=lista, color=discord.Color.gold())
    embed.set_footer(text="Carabineros de Chile")
    await ctx.send(embed=embed, delete_after=45)

# --- COMANDO PARAR (REGISTRO DE FALTA) ---
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
        
        await ctx.send(embed=discord.Embed(
            title="⚠️ SANCIÓN ADMINISTRATIVA",
            description=f"Se ha procedido al cierre forzado del servicio para el oficial {miembro.mention}.\n**Motivo:** Incumplimiento de protocolo (AFK/Abuso).",
            color=discord.Color.orange()
        ))

        canal = bot.get_channel(ID_CANAL_PRIVADO)
        if canal:
            reporte = discord.Embed(title="🚨 REGISTRO DE FALTA - CARABINEROS DE CHILE", color=discord.Color.red())
            reporte.set_thumbnail(url=miembro.display_avatar.url)
            reporte.add_field(name="👮 Oficial Sancionado", value=miembro.mention, inline=False)
            reporte.add_field(name="🛡️ Aplicado por", value=ctx.author.mention, inline=True)
            reporte.add_field(name="⏳ Tiempo Acumulado", value=f"{h}h {m}m", inline=True)
            reporte.set_footer(text=f"Fecha: {ahora.strftime('%d/%m/%Y')} | Falta Administrativa Carabineros")
            await canal.send(embed=reporte)

bot.run(TOKEN)
