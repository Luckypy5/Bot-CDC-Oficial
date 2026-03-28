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

# --- MISIONES ---
misiones_dict = {
    0: "LUNES: 'Papeles en Regla' - Fiscalización técnica en Peajes.",
    1: "MARTES: 'Identidad de Bloque' - Saturación en callejones de LS.",
    2: "MIÉRCOLES: 'Binomio Los Santos' - Patrullaje motorizado.",
    3: "JUEVES: 'Ruta Segura' - Escolta oficial a camiones.",
    4: "VIERNES: 'Día de Especialista' - Operativo especial (GOPE/SIP).",
    5: "SÁBADO: 'Saturación Central' - Control masivo de baúles.",
    6: "DOMINGO: 'Vigilancia Rural' - Vigilancia en sectores alejados."
}

intents = discord.Intents.default()
intents.message_content = True 
bot = commands.Bot(command_prefix='!', intents=intents)
turnos_activos = {}

@bot.event
async def on_ready():
    print(f'✅ Sistema CDC Finalizado | Franco, el bot está al 100% de su capacidad.')

# --- TAREA AUTOMÁTICA MISIONES ---
@tasks.loop(time=datetime.time(hour=0, minute=0, tzinfo=ZONA_HORARIA))
async def enviar_mision_diaria():
    canal = bot.get_channel(ID_CANAL_MISIONES)
    if canal:
        try: await canal.purge(limit=10) 
        except: pass
        dia = datetime.datetime.now(ZONA_HORARIA).weekday()
        embed = discord.Embed(title="📅 HOJA DE RUTA DIARIA - CDC", description=f"**Misión:** {misiones_dict[dia]}", color=discord.Color.blue())
        await canal.send(embed=embed)
        embed_bono = discord.Embed(title="💰 BONO POR ACTIVIDAD", description="Cumplir **3 misiones semanales** otorga un bono en su liquidación.", color=discord.Color.gold())
        await canal.send(embed=embed_bono)

# --- COMANDOS DE ASISTENCIA ---
@bot.command(name="inicio")
async def inicio(ctx):
    try: await ctx.message.delete()
    except: pass
    if ctx.author.id in turnos_activos:
        return await ctx.send(f"⚠️ Ya estás en servicio.", delete_after=5)
    turnos_activos[ctx.author.id] = datetime.datetime.now(ZONA_HORARIA)
    embed = discord.Embed(title="🟢 INICIO DE SERVICIO", description=f"Oficial **{ctx.author.mention}** ha iniciado funciones.", color=discord.Color.from_rgb(0, 104, 71))
    await ctx.send(embed=embed)

@bot.command(name="termino")
async def termino(ctx):
    try: await ctx.message.delete()
    except: pass
    if ctx.author.id not in turnos_activos: return
    inicio_t = turnos_activos.pop(ctx.author.id)
    ahora = datetime.datetime.now(ZONA_HORARIA)
    duracion = ahora - inicio_t
    h, r = divmod(int(duracion.total_seconds()), 3600)
    m, _ = divmod(r, 60)
    await ctx.send(embed=discord.Embed(title="🔴 TÉRMINO DE SERVICIO", description=f"Oficial **{ctx.author.mention}** finaliza funciones.", color=discord.Color.from_rgb(180, 0, 0)))
    canal = bot.get_channel(ID_CANAL_PRIVADO)
    if canal:
        reporte = discord.Embed(title="📄 BITÁCORA DE GUARDIA", color=discord.Color.dark_green())
        reporte.add_field(name="👮 Oficial", value=ctx.author.mention)
        reporte.add_field(name="⏳ Jornada", value=f"{h}h {m}m")
        await canal.send(embed=reporte)

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
        
        # AVISO PÚBLICO DE FALTA
        embed_falta = discord.Embed(
            title="⚠️ SANCIÓN ADMINISTRATIVA",
            description=f"Se ha procedido al cierre forzado del servicio para el oficial {miembro.mention}.\n**Motivo:** Incumplimiento de protocolo (AFK/Abuso).",
            color=discord.Color.orange()
        )
        await ctx.send(embed=embed_falta)

        # REPORTE PARA JEFATURA
        canal = bot.get_channel(ID_CANAL_PRIVADO)
        if canal:
            reporte = discord.Embed(title="🚨 REGISTRO DE FALTA - JEFATURA", color=discord.Color.red())
            reporte.set_thumbnail(url=miembro.display_avatar.url)
            reporte.add_field(name="👮 Oficial Sancionado", value=miembro.mention, inline=False)
            reporte.add_field(name="🛡️ Aplicado por", value=ctx.author.mention, inline=True)
            reporte.add_field(name="⏳ Tiempo Acumulado", value=f"{h}h {m}m", inline=True)
            reporte.add_field(name="📋 Estado", value="**FALTA REGISTRADA**", inline=False)
            reporte.set_footer(text=f"Fecha: {ahora.strftime('%d/%m/%Y')}")
            await canal.send(embed=reporte)

@bot.command(name="activos")
async def activos(ctx):
    try: await ctx.message.delete()
    except: pass
    if not turnos_activos: return await ctx.send("No hay unidades en frecuencia.", delete_after=5)
    lista = "\n".join([f"• <@{uid}>" for uid in turnos_activos.keys()])
    await ctx.send(embed=discord.Embed(title="🚔 UNIDADES EN 10-39", description=lista, color=discord.Color.gold()), delete_after=30)

bot.run(TOKEN)
