"""
tests/test_transcription.py
Suite integral de pruebas unitarias para scripts/01_transcribir.py.
Cubre:
1. Detección de audios (.wav y otras extensiones compatibles).
2. Cálculo de rutas y preservación de subdirectorios.
3. Creación de archivos TXT y cálculo de duración.
4. Preservación estricta de transcripciones existentes (no sobrescritura).
5. Habilitación explícita de --overwrite.
6. Manejo de múltiples audios en lote.
7. Manejo y registro de errores individuales sin abortar ejecución.
8. Generación del CSV de resumen.
9. Validación de carpeta inexistente.
10. Descompresión de archivos ZIP y errores de ZIP.
11. Argumentos CLI y ejecución con --help.
"""
import zipfile
import importlib.util
from pathlib import Path
from unittest.mock import MagicMock, patch
import pytest
import pandas as pd

ROOT_DIR = Path(__file__).resolve().parent.parent
spec = importlib.util.spec_from_file_location("transcribir_mod", ROOT_DIR / "scripts" / "01_transcribir.py")
transcribir_mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(transcribir_mod)

descomprimir_zip = transcribir_mod.descomprimir_zip
encontrar_audios = transcribir_mod.encontrar_audios
calcular_duracion = transcribir_mod.calcular_duracion
transcribir_audio = transcribir_mod.transcribir_audio
guardar_transcripcion = transcribir_mod.guardar_transcripcion
procesar_audio = transcribir_mod.procesar_audio
guardar_resumen = transcribir_mod.guardar_resumen
parsear_argumentos = transcribir_mod.parsear_argumentos
ejecutar_pipeline_transcripcion = transcribir_mod.ejecutar_pipeline_transcripcion
main = transcribir_mod.main

# ------------------------------------------------------------------------------
# 1. Detección de audios (.wav y extensiones compatibles)
# ------------------------------------------------------------------------------
def test_deteccion_audios_wav_y_extensiones(tmp_path):
    """Verifica detección de .wav y otros formatos de audio, excluyendo archivos no soportados."""
    dir_audios = tmp_path / "audios"
    dir_audios.mkdir()
    
    (dir_audios / "audio1.wav").write_bytes(b"dummy wav")
    (dir_audios / "audio2.mp3").write_bytes(b"dummy mp3")
    (dir_audios / "audio3.M4A").write_bytes(b"dummy m4a")
    
    sub = dir_audios / "subcarpeta"
    sub.mkdir()
    (sub / "audio4.flac").write_bytes(b"dummy flac")
    (sub / "audio5.ogg").write_bytes(b"dummy ogg")
    
    # No compatibles
    (dir_audios / "documento.pdf").write_bytes(b"dummy pdf")
    (dir_audios / "datos.csv").write_bytes(b"dummy csv")
    (sub / "codigo.py").write_bytes(b"dummy py")
    
    audios = encontrar_audios(dir_audios)
    nombres = {a.name.lower() for a in audios}
    
    assert len(audios) == 5
    assert nombres == {"audio1.wav", "audio2.mp3", "audio3.m4a", "audio4.flac", "audio5.ogg"}

# ------------------------------------------------------------------------------
# 2. Rutas y subdirectorios
# ------------------------------------------------------------------------------
def test_rutas_subdirectorios(tmp_path):
    """Verifica que procesar_audio conserve la jerarquía relativa de subcarpetas si aplica."""
    dir_base = tmp_path / "audios"
    dir_salida = tmp_path / "transcripciones"
    dir_base.mkdir()
    dir_salida.mkdir()
    
    sub = dir_base / "Humanos"
    sub.mkdir()
    audio = sub / "llamada_01.wav"
    audio.write_bytes(b"dummy")
    
    mock_modelo = MagicMock()
    mock_modelo.transcribe.return_value = {"text": "Texto prueba", "segments": [{"end": 12.5}]}
    
    res = procesar_audio(
        ruta_audio=audio,
        modelo=mock_modelo,
        dir_salida=dir_salida,
        dir_base_entrada=dir_base
    )
    
    ruta_txt_esperada = dir_salida / "Humanos" / "llamada_01.txt"
    assert Path(res["ruta_txt"]) == ruta_txt_esperada
    assert ruta_txt_esperada.exists()
    assert ruta_txt_esperada.read_text(encoding="utf-8") == "Texto prueba"

# ------------------------------------------------------------------------------
# 3. Cálculo de duración
# ------------------------------------------------------------------------------
def test_calcular_duracion():
    """Comprueba el cálculo de duración a partir de segments de Whisper."""
    # Caso normal con múltiples segmentos
    res_normal = {
        "segments": [
            {"start": 0.0, "end": 4.5, "text": "Hola"},
            {"start": 4.5, "end": 18.2, "text": "Buenas tardes"}
        ]
    }
    assert calcular_duracion(res_normal) == 18.2
    
    # Caso segmentos vacíos
    assert calcular_duracion({"segments": []}) == 0.0
    
    # Caso sin segments
    assert calcular_duracion({}) == 0.0
    assert calcular_duracion(None) == 0.0

# ------------------------------------------------------------------------------
# 4. Creación de TXT y resumen CSV
# ------------------------------------------------------------------------------
def test_creacion_txt_y_resumen_csv(tmp_path):
    """Comprueba la generación correcta del .txt y del archivo CSV de resumen."""
    in_dir = tmp_path / "in"
    out_dir = tmp_path / "out"
    in_dir.mkdir()
    out_dir.mkdir()
    
    audio = in_dir / "llamada.wav"
    audio.write_bytes(b"dummy audio")
    
    mock_modelo = MagicMock()
    mock_modelo.transcribe.return_value = {
        "text": "Buenos días hablo con el señor Pérez",
        "segments": [{"end": 45.0}]
    }
    
    pipeline_res = ejecutar_pipeline_transcripcion(
        dir_entrada=in_dir,
        dir_salida=out_dir,
        modelo_precargado=mock_modelo
    )
    
    assert pipeline_res["procesados"] == 1
    txt_file = out_dir / "llamada.txt"
    assert txt_file.exists()
    assert "Buenos días hablo con el señor Pérez" in txt_file.read_text(encoding="utf-8")
    
    csv_file = out_dir / "transcripciones_resumen.csv"
    assert csv_file.exists()
    df_csv = pd.read_csv(csv_file)
    assert len(df_csv) == 1
    assert df_csv.loc[0, "archivo"] == "llamada.wav"
    assert df_csv.loc[0, "duracion_segundos"] == 45.0
    assert df_csv.loc[0, "estado"] == "procesado"

# ------------------------------------------------------------------------------
# 5. Inmutabilidad (No sobrescritura por defecto)
# ------------------------------------------------------------------------------
def test_no_sobrescritura_por_defecto(tmp_path):
    """
    CRÍTICO: Comprueba que una transcripción existente jamás sea sobrescrita
    por defecto, preservando el contenido original sin invocar a Whisper.
    """
    in_dir = tmp_path / "in"
    out_dir = tmp_path / "out"
    in_dir.mkdir()
    out_dir.mkdir()
    
    audio = in_dir / "audio_existente.wav"
    audio.write_bytes(b"dummy audio")
    
    txt_existente = out_dir / "audio_existente.txt"
    contenido_inmutable = "Transcripción histórica aprobada que NO debe ser tocada."
    txt_existente.write_text(contenido_inmutable, encoding="utf-8")
    
    mock_modelo = MagicMock()
    
    pipeline_res = ejecutar_pipeline_transcripcion(
        dir_entrada=in_dir,
        dir_salida=out_dir,
        overwrite=False,
        modelo_precargado=mock_modelo
    )
    
    assert pipeline_res["omitidos"] == 1
    assert pipeline_res["procesados"] == 0
    # El archivo conserva exactamente su texto previo
    assert txt_existente.read_text(encoding="utf-8") == contenido_inmutable
    # Whisper no fue llamado
    mock_modelo.transcribe.assert_not_called()

# ------------------------------------------------------------------------------
# 6. Flag --overwrite
# ------------------------------------------------------------------------------
def test_flag_overwrite(tmp_path):
    """Comprueba que al activar overwrite=True se actualice el archivo .txt existente."""
    in_dir = tmp_path / "in"
    out_dir = tmp_path / "out"
    in_dir.mkdir()
    out_dir.mkdir()
    
    audio = in_dir / "audio_a_renovar.wav"
    audio.write_bytes(b"dummy")
    
    txt_file = out_dir / "audio_a_renovar.txt"
    txt_file.write_text("Texto viejo", encoding="utf-8")
    
    mock_modelo = MagicMock()
    mock_modelo.transcribe.return_value = {
        "text": "Texto nuevo y actualizado",
        "segments": [{"end": 30.0}]
    }
    
    pipeline_res = ejecutar_pipeline_transcripcion(
        dir_entrada=in_dir,
        dir_salida=out_dir,
        overwrite=True,
        modelo_precargado=mock_modelo
    )
    
    assert pipeline_res["procesados"] == 1
    assert pipeline_res["omitidos"] == 0
    assert txt_file.read_text(encoding="utf-8") == "Texto nuevo y actualizado"

# ------------------------------------------------------------------------------
# 7. Múltiples audios en lote
# ------------------------------------------------------------------------------
def test_multiples_audios_procesamiento(tmp_path):
    """Verifica el procesamiento ordenado de múltiples audios."""
    in_dir = tmp_path / "in"
    out_dir = tmp_path / "out"
    in_dir.mkdir()
    out_dir.mkdir()
    
    for i in range(3):
        (in_dir / f"audio_{i}.wav").write_bytes(f"dummy {i}".encode())
        
    mock_modelo = MagicMock()
    mock_modelo.transcribe.side_effect = [
        {"text": "Llamada 0", "segments": [{"end": 10.0}]},
        {"text": "Llamada 1", "segments": [{"end": 20.0}]},
        {"text": "Llamada 2", "segments": [{"end": 30.0}]},
    ]
    
    pipeline_res = ejecutar_pipeline_transcripcion(
        dir_entrada=in_dir,
        dir_salida=out_dir,
        modelo_precargado=mock_modelo
    )
    
    assert pipeline_res["total"] == 3
    assert pipeline_res["procesados"] == 3
    assert (out_dir / "audio_0.txt").read_text(encoding="utf-8") == "Llamada 0"
    assert (out_dir / "audio_1.txt").read_text(encoding="utf-8") == "Llamada 1"
    assert (out_dir / "audio_2.txt").read_text(encoding="utf-8") == "Llamada 2"

# ------------------------------------------------------------------------------
# 8. Errores individuales no abortan ejecución
# ------------------------------------------------------------------------------
def test_errores_individuales_no_detienen_proceso(tmp_path):
    """Comprueba que si un archivo falla, los demás audios continúen transcribiéndose."""
    in_dir = tmp_path / "in"
    out_dir = tmp_path / "out"
    in_dir.mkdir()
    out_dir.mkdir()
    
    (in_dir / "audio_ok.wav").write_bytes(b"dummy ok")
    (in_dir / "audio_falla.wav").write_bytes(b"dummy corrupt")
    
    mock_modelo = MagicMock()
    def transcribe_side_effect(ruta, **kwargs):
        if "audio_falla" in str(ruta):
            raise ValueError("Encabezado WAV corrupto")
        return {"text": "Audio correcto", "segments": [{"end": 15.0}]}
        
    mock_modelo.transcribe.side_effect = transcribe_side_effect
    
    pipeline_res = ejecutar_pipeline_transcripcion(
        dir_entrada=in_dir,
        dir_salida=out_dir,
        modelo_precargado=mock_modelo
    )
    
    assert pipeline_res["total"] == 2
    assert pipeline_res["procesados"] == 1
    assert pipeline_res["errores"] == 1
    assert (out_dir / "audio_ok.txt").exists()
    assert not (out_dir / "audio_falla.txt").exists()

# ------------------------------------------------------------------------------
# 9. Carpeta inexistente
# ------------------------------------------------------------------------------
def test_carpeta_inexistente(tmp_path):
    """Comprueba el manejo elegante cuando el directorio no existe."""
    dir_invalido = tmp_path / "carpeta_que_no_existe"
    audios = encontrar_audios(dir_invalido)
    assert audios == []
    
    pipeline_res = ejecutar_pipeline_transcripcion(
        dir_entrada=dir_invalido,
        dir_salida=tmp_path / "out"
    )
    assert pipeline_res["total"] == 0
    assert pipeline_res["procesados"] == 0

# ------------------------------------------------------------------------------
# 10. Descompresión de archivos ZIP y errores de ZIP
# ------------------------------------------------------------------------------
def test_descomprimir_zip_y_procesar(tmp_path):
    """Comprueba el flujo opcional de descompresión de archivo .zip con audios."""
    zip_path = tmp_path / "audios_empaquetados.zip"
    dest_dir = tmp_path / "extraidos"
    out_dir = tmp_path / "txt_out"
    
    # Crear un ZIP válido con 1 audio
    with zipfile.ZipFile(zip_path, "w") as z:
        z.writestr("llamada_zip.wav", b"dummy audio inside zip")
        
    mock_modelo = MagicMock()
    mock_modelo.transcribe.return_value = {
        "text": "Transcripcion desde archivo zip",
        "segments": [{"end": 22.0}]
    }
    
    pipeline_res = ejecutar_pipeline_transcripcion(
        dir_entrada=dest_dir,
        dir_salida=out_dir,
        ruta_zip=zip_path,
        modelo_precargado=mock_modelo
    )
    
    assert pipeline_res["total"] == 1
    assert pipeline_res["procesados"] == 1
    assert (out_dir / "llamada_zip.txt").read_text(encoding="utf-8") == "Transcripcion desde archivo zip"

def test_descomprimir_zip_errores(tmp_path):
    """Verifica las excepciones al recibir ZIP inexistente o corrupto."""
    zip_falso = tmp_path / "no_existe.zip"
    with pytest.raises(FileNotFoundError):
        descomprimir_zip(zip_falso, tmp_path / "dest")
        
    zip_corrupto = tmp_path / "corrupto.zip"
    zip_corrupto.write_bytes(b"esto no es un zip")
    with pytest.raises(zipfile.BadZipFile):
        descomprimir_zip(zip_corrupto, tmp_path / "dest")

# ------------------------------------------------------------------------------
# 11. Argumentos CLI y --help
# ------------------------------------------------------------------------------
def test_argumentos_cli_parser():
    """Verifica que el parser de argumentos interprete correctamente las banderas."""
    args = parsear_argumentos([
        "--input", "mis_audios",
        "--output", "mis_txts",
        "--tipo-agente", "ia",
        "--model", "medium",
        "--language", "es",
        "--overwrite"
    ])
    assert args.input == Path("mis_audios")
    assert args.output == Path("mis_txts")
    assert args.tipo_agente == "ia"
    assert args.model == "medium"
    assert args.language == "es"
    assert args.overwrite is True

def test_argumentos_cli_help():
    """Verifica que main() con --help salga con código 0."""
    with pytest.raises(SystemExit) as excinfo:
        main(["--help"])
    assert excinfo.value.code == 0
