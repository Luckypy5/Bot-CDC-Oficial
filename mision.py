import discord
from discord.ext import commands, tasks
import datetime
import pytz
import random

# --- CONFIGURACIÓN DE IDENTIDAD ---
TOKEN = 'MTQ3ODQ2NDA0MDAwNjA2MjEyNA.GM24GF.HIqN4P5mhfQvNmQKAAv0e9aRcKNCjrjn-pvGU4'
ID_CANAL_MISIONES = 1478505943711875112  # ID del canal #misiones-diarias
ID_CANAL_TURNOS = 1473131173088723134    # ID del canal #registro-de-servicio
ZONA_HORARIA = pytz.timezone('America/Santiago')

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix='!', intents=intents)

# --- BASE DE DATOS TEMPORAL DE TURNOS ---
turnos_activos = {} # Guarda el ID del usuario y su hora de entrada

# --- CATÁLOGO DE MISIONES OFICIALES ---
misiones_semanales = {
    0: {"t": "Operación: 'Código 1' (Robo a Tienda) 🚨", "d": "Atender 3 llamados de robo a tiendas (24/7, licorerías).", "e": "Foto de patrulla o sospechoso bajo custodia."},
    1: {"t": "Operación: 'Saturación en los Bloques' (Barrio SERVIU) 🏘️", "d": "Patrullaje preventivo y realizar al menos 2 controles de identidad.", "e": "Foto de oficiales patrullando a pie o fiscalizando."},
    2: {"t": "Operación: 'Escolta Ruta 5' (Solo Camioneros) 🚛", "d": "Ubicar a un Camionero y ofrecerle protección de ruta.", "e": "Foto de la unidad junto al camión en carretera."},
    3: {"t": "Operación: 'Control de Peaje / Aduana' 🛣️", "d": "Punto de control en peaje principal. Revisar documentos y maletero.", "e": "Foto de vehículo civil siendo fiscalizado."},
    4: {"t": "Operación: 'Patrullaje de Infantería' (A Pie/Bici) 🚲🚶‍♂️", "d": "Recorrer plazas o paseos peatonales e interactuar con civiles.", "e": "Foto del oficial con civiles o en zona peatonal."},
    5: {"t": "Operación: 'Unidad Motorizada (Binomio)' 🏍️", "d": "Patrullaje en pareja (2 motos) por tráfico o cerros.", "e": "Foto de las dos motos CDC juntas en operativo."},
    6: {"t": "Operación: 'Despliegue de Soberanía' (Convoy La Moneda) 🏛️", "d": "Viaje grupal (mínimo 3 unidades) hasta el Palacio de La Moneda.", "e": "Foto grupal frente al palacio."}
}

# --- COMANDOS DE RELOJ DE SERVICIO ---
@bot.command()
async def entrar(ctx):
    """Registra el inicio de turno (10-39)"""
    if ctx.channel.id != ID_CANAL_TURNOS:
        return await ctx.send(f"⚠️ Este comando solo funciona en el canal de registros.")

    if ctx.author.id in turnos_activos:
        await ctx.send(f"⚠️ {ctx.author.mention}, ya te encuentras en servicio activo.")
    else:
        # Guarda la hora exacta de entrada
        turnos_activos[ctx.author.id] = datetime.datetime.now(ZONA_HORARIA)
        await ctx.send(f"🟢 *10-39 (Inicio de Turno)*\nOficial: {ctx.author.mention}\nHora: {datetime.datetime.now(ZONA_HORARIA).strftime('%H:%M')} hrs.\n¡Buen servicio!")

@bot.command()
async def salir(ctx):
    """Registra el fin de turno (10-10) y calcula el tiempo"""
    if ctx.channel.id != ID_CANAL_TURNOS:
        return await ctx.send(f"⚠️ Este comando solo funciona en el canal de registros.")

    if ctx.author.id not in turnos_activos:
        await ctx.send(f"❌ {ctx.author.mention}, no has iniciado turno (10-39) todavía.")
    else:
        inicio = turnos_activos.pop(ctx.author.id)
        fin = datetime.datetime.now(ZONA_HORARIA)
        
        # Cálculo de tiempo patrullado
        diferencia = fin - inicio
        horas, segundos = divmod(diferencia.total_seconds(), 3600)
        minutos = (segundos // 60)
        
        embed = discord.Embed(title="🔴 10-10 (Fin de Turno)", color=discord.Color.red())
        embed.add_field(name="Oficial", value=ctx.author.mention, inline=False)
        embed.add_field(name="Tiempo en Servicio", value=f"{int(horas)} horas y {int(minutos)} minutos", inline=False)
        embed.set_footer(text="Registro de Actividad CDC")
        await ctx.send(embed=embed)

# --- COMANDO EXTRA (LEY DE ALCOHOLES) ---
@bot.command()
async def extra(ctx):
    """Misión aleatoria para operativos sorpresa"""
    folio = random.randint(1000, 9999)
    embed = discord.Embed(
        title="🚨 OPERATIVO: Fiscalización de Tránsito",
        description=f"*FOLIO: #EXT-{folio}\n\nTarea:* Buscar infractores (choques, veredas) y aplicar Ley de Alcoholes.\n*Objetivo:* Aplicar multa según Tabla Oficial.\n*Evidencia:* Captura de la multa en el chat.",
        color=discord.Color.gold()
    )
    await ctx.send(embed=embed)

# --- TAREA AUTOMÁTICA DE MISIONES ---
@tasks.loop(hours=24)
async def enviar_mision_diaria():
    canal = bot.get_channel(ID_CANAL_MISIONES)
    if canal:
        dia_semana = datetime.datetime.now(ZONA_HORARIA).weekday()
        m = misiones_semanales[dia_semana]
        folio = random.randint(1000, 9999)
        
        embed = discord.Embed(title=m['t'], color=discord.Color.green())
        embed.add_field(name="Folio de Registro", value=f"#CDC-{folio}", inline=False)
        embed.add_field(name="Tarea", value=m['d'], inline=False)
        embed.add_field(name="Evidencia", value=m['e'], inline=False)
        embed.set_footer(text="Unidad de Operaciones CDC - 2026")
        await canal.send(embed=embed)

@bot.event
async def on_ready():
    print(f'✅ Sistema Centralizado CDC en línea: {bot.user}')
    if not enviar_mision_diaria.is_running():
        enviar_mision_diaria.start()

bot.run(TOKEN)
