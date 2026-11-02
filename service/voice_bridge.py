"""Explicit audio transcription through the installed Muse CLI; no stored recordings."""
import base64
import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import muse_bridge
try:
    import imageio_ffmpeg
except ImportError:
    imageio_ffmpeg=None


def transcribe(body):
    if not isinstance(body,dict) or not isinstance(body.get('audio'),str):
        raise ValueError('No se recibió una grabación WAV.')
    encoded=body['audio']
    if len(encoded)>4000000:
        raise ValueError('La grabación supera el límite. Graba hasta un minuto.')
    try:
        audio=base64.b64decode(encoded,validate=True)
    except (ValueError,TypeError):
        raise ValueError('Grabación inválida.') from None
    if len(audio)<44 or audio[:4]!=b'RIFF' or audio[8:12]!=b'WAVE':
        raise ValueError('La grabación debe ser un archivo WAV.')
    exe=muse_bridge.binary()
    if not exe:raise ValueError('Muse Code no está instalado en este equipo.')
    with tempfile.TemporaryDirectory(prefix='bee-muse-voice-') as folder:
        clip=Path(folder)/'voice.wav'
        clip.write_bytes(audio)
        env=os.environ.copy()
        if not shutil.which('ffmpeg'):
            if imageio_ffmpeg is None:
                raise ValueError('Falta el decodificador de audio. Instala requirements-voice.txt o usa el paquete de escritorio actualizado.')
            decoder=Path(folder)/('ffmpeg.exe' if os.name=='nt' else 'ffmpeg')
            shutil.copy2(imageio_ffmpeg.get_ffmpeg_exe(),decoder)
            decoder.chmod(decoder.stat().st_mode|0o111)
            env['PATH']=folder+os.pathsep+env.get('PATH','')
        try:
            result=subprocess.run([str(exe),'voice','transcribe',str(clip)],cwd=folder,
                stdin=subprocess.DEVNULL,stdout=subprocess.PIPE,stderr=subprocess.PIPE,
                timeout=120,shell=False,encoding='utf-8',errors='replace',
                creationflags=getattr(subprocess,'CREATE_NO_WINDOW',0),env=env)
        except subprocess.TimeoutExpired:
            raise ValueError('La transcripción de Muse agotó el tiempo de espera.') from None
        if result.returncode or not result.stdout.strip():
            if 'no audio decoder on this host' in result.stderr:
                raise ValueError('El comando de voz de Muse no pudo usar el decodificador de audio de este sistema. La grabación no se transcribió; esta integración requiere comprobar el soporte del CLI en esta plataforma.')
            raise ValueError('Muse no pudo transcribir el audio. Comprueba tu sesión y acceso a voz en Meta.')
        return {'text':result.stdout.strip()[:12000],'provider':'Muse Voice Transcribe · Meta',
                'scope':'Grabación enviada a Meta para transcribir. No se conserva el audio en Bee-Muse.'}
