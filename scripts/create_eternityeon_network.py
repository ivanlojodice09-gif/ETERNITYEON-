# ==============================================================================
# ETERNITYEON - TouchDesigner Network Structure & Setup Script
# Repository: ivanlojodice09-gif/ETERNITYEON-
# Versione revisionata: 1.0
# Descrizione:
#   Crea una rete stabile e funzionante in TouchDesigner con:
#   - Audio In
#   - OSC In
#   - Serial In (Arduino USB)
#   - Noise TOP
#   - Processing visuale
#   - Window output
# ==============================================================================

import op

def create_eternityeon_network():
    """
    Crea una rete TouchDesigner stabile per ETERNITYEON.
    L'input reale viene gestito da:
    - Arduino via seriale
    - ESP32 / bridge OSC via UDP
    - Microfono / Audio In
    """
    root = op('/project1')
    if root is None:
        print("Errore: /project1 non trovato. Apri il progetto principale di TouchDesigner.")
        return None

    existing = root.op('ETERNITYEON')
    if existing:
        print("Nodo ETERNITYEON già presente. Verrà rimosso.")
        existing.destroy()

    # --------------------------------------------------------------------------
    # 1. CONTAINER PRINCIPALE
    # --------------------------------------------------------------------------
    base = root.create(baseCOMP, 'ETERNITYEON')
    base.nodeX = 0
    base.nodeY = 0

    # --------------------------------------------------------------------------
    # 2. INPUT AUDIO E SENSORIALI
    # --------------------------------------------------------------------------
    audio_in = base.create(audioInCHOP, 'audio_in')
    audio_in.nodeX = -1000
    audio_in.nodeY = 300

    audio_spec = base.create(audioSpectrumCHOP, 'audio_spectrum')
    audio_spec.inputConnectors[0].connect(audio_in.outputConnectors[0])
    audio_spec.nodeX = -800
    audio_spec.nodeY = 300

    audio_rms = base.create(analyzeCHOP, 'audio_rms')
    audio_rms.par.function = 4
    audio_rms.inputConnectors[0].connect(audio_in.outputConnectors[0])
    audio_rms.nodeX = -800
    audio_rms.nodeY = 180

    audio_smooth = base.create(filterCHOP, 'audio_smooth')
    audio_smooth.par.filtertype = 0
    audio_smooth.par.filterwidth = 0.1
    audio_smooth.inputConnectors[0].connect(audio_rms.outputConnectors[0])
    audio_smooth.nodeX = -600
    audio_smooth.nodeY = 180

    osc_in = base.create(oscInCHOP, 'osc_sensors')
    osc_in.par.port = 10000
    osc_in.nodeX = -1000
    osc_in.nodeY = 0

    serial_in = base.create(serialInCHOP, 'arduino_serial')
    serial_in.par.port = 0
    serial_in.par.baudrate = 9600
    serial_in.nodeX = -1000
    serial_in.nodeY = -150

    math_serial = base.create(mathCHOP, 'math_serial')
    math_serial.par.gain1 = 1.0
    math_serial.inputConnectors[0].connect(serial_in.outputConnectors[0])
    math_serial.nodeX = -800
    math_serial.nodeY = -150

    merge_sensors = base.create(mergeCHOP, 'merge_sensors')
    merge_sensors.inputConnectors[0].connect(osc_in.outputConnectors[0])
    merge_sensors.inputConnectors[1].connect(math_serial.outputConnectors[0])
    merge_sensors.nodeX = -600
    merge_sensors.nodeY = -75

    math_sensors = base.create(mathCHOP, 'math_sensors')
    math_sensors.inputConnectors[0].connect(merge_sensors.outputConnectors[0])
    math_sensors.nodeX = -450
    math_sensors.nodeY = -75

    # --------------------------------------------------------------------------
    # 3. GENERATIVE VISUAL
    # --------------------------------------------------------------------------
    noise_gen = base.create(noiseTOP, 'noise_gen')
    noise_gen.par.resolutionw = 1920
    noise_gen.par.resolutionh = 1080
    noise_gen.par.period = 3.0
    noise_gen.par.harmonics = 3
    noise_gen.par.tz.expr = "abs(seconds) * 0.2 + op('audio_smooth')[0] * 1.5"
    noise_gen.nodeX = -300
    noise_gen.nodeY = -100

    comp_out = base.create(compositeTOP, 'comp_out')
    comp_out.par.operand = 0
    comp_out.inputConnectors[0].connect(noise_gen.outputConnectors[0])
    comp_out.nodeX = 100
    comp_out.nodeY = -100

    level_out = base.create(levelTOP, 'level_master')
    level_out.par.brightness.expr = "1.0 + op('math_sensors')[0] * 0.5"
    level_out.inputConnectors[0].connect(comp_out.outputConnectors[0])
    level_out.nodeX = 350
    level_out.nodeY = -100

    null_out = base.create(nullTOP, 'OUT_VISUAL')
    null_out.inputConnectors[0].connect(level_out.outputConnectors[0])
    null_out.nodeX = 600
    null_out.nodeY = -100

    # --------------------------------------------------------------------------
    # 4. WINDOW OUTPUT
    # --------------------------------------------------------------------------
    window_comp = base.create(windowCOMP, 'output_window')
    window_comp.par.top = null_out.path
    window_comp.par.winopen = 1
    window_comp.nodeX = 850
    window_comp.nodeY = -100

    print("SUCCESS: Rete ETERNITYEON creata correttamente in /project1/ETERNITYEON")
    return base

# Esecuzione
create_eternityeon_network()
