const puppeteer = require('puppeteer-core');
const { spawn } = require('child_process');
const fs = require('fs');
const path = require('path');

async function renderHtmlToVideo({
  inputUrl,
  outputPath,
  duration = 8,
  fps = 30,
  width = 1080,
  height = 1920,
  audioPath = null,
  musicBpm = 120
}) {
  const totalFrames = Math.round(duration * fps);
  console.log(`[VideoRender] Iniciando render: ${width}x${height} @ ${fps}fps, ${duration}s (${totalFrames} frames)`);
  console.log(`[VideoRender] URL de origen: ${inputUrl}`);
  console.log(`[VideoRender] Archivo de salida: ${outputPath}`);

  const browser = await puppeteer.launch({
    executablePath: '/usr/bin/google-chrome',
    args: [
      '--no-sandbox',
      '--disable-setuid-sandbox',
      '--disable-dev-shm-usage',
      '--disable-gpu',
      '--headless=new',
      `--window-size=${width},${height}`
    ],
    defaultViewport: {
      width,
      height,
      deviceScaleFactor: 1
    }
  });

  const page = await browser.newPage();
  await page.goto(inputUrl, { waitUntil: 'networkidle0', timeout: 30000 });

  // Pausar todas las animaciones W3C Web Animations para control determinista
  await page.evaluate(() => {
    document.getAnimations().forEach(anim => anim.pause());
    window.__totalAnimations = document.getAnimations().length;
    console.log("Animaciones detectadas:", window.__totalAnimations);
  });

  // Configurar FFmpeg pipe
  const ffmpegArgs = [
    '-y',
    '-f', 'image2pipe',
    '-vcodec', 'png',
    '-r', String(fps),
    '-i', '-',
  ];

  if (audioPath && fs.existsSync(audioPath)) {
    ffmpegArgs.push('-i', audioPath);
    ffmpegArgs.push('-c:v', 'libx264', '-pix_fmt', 'yuv420p', '-preset', 'veryfast', '-c:a', 'aac', '-b:a', '192k', '-shortest');
  } else {
    ffmpegArgs.push('-c:v', 'libx264', '-pix_fmt', 'yuv420p', '-preset', 'veryfast');
  }

  ffmpegArgs.push(outputPath);

  const ffmpeg = spawn('ffmpeg', ffmpegArgs);

  ffmpeg.stderr.on('data', (data) => {
    // console.log(`ffmpeg: ${data}`);
  });

  ffmpeg.on('error', (err) => {
    console.error(`[VideoRender] Error en FFmpeg:`, err);
  });

  console.log(`[VideoRender] Capturando frames deterministas...`);
  const startTime = Date.now();

  for (let f = 0; f < totalFrames; f++) {
    const currentTimeMs = (f / fps) * 1000;

    // Sincronizar tiempo de animaciones
    await page.evaluate((timeMs, frameIndex, maxFrames) => {
      document.getAnimations().forEach(anim => {
        anim.pause();
        anim.currentTime = timeMs;
      });
      if (typeof window.seekFrame === 'function') {
        window.seekFrame(timeMs / 1000, frameIndex, maxFrames);
      }
    }, currentTimeMs, f, totalFrames);

    // Capturar frame en PNG
    const buffer = await page.screenshot({
      type: 'png',
      omitBackground: false
    });

    // Enviar al pipe de FFmpeg
    ffmpeg.stdin.write(buffer);

    if (f % (fps * 2) === 0 || f === totalFrames - 1) {
      const pct = Math.round((f / totalFrames) * 100);
      console.log(`[VideoRender] Progreso: ${pct}% (Frame ${f}/${totalFrames})`);
    }
  }

  ffmpeg.stdin.end();

  await new Promise((resolve, reject) => {
    ffmpeg.on('close', (code) => {
      if (code === 0) {
        resolve();
      } else {
        reject(new Error(`FFmpeg finalizó con código de error ${code}`));
      }
    });
  });

  await browser.close();

  const elapsed = ((Date.now() - startTime) / 1000).toFixed(1);
  console.log(`[VideoRender] ¡Video generado con éxito en ${elapsed}s! -> ${outputPath}`);
}

module.exports = { renderHtmlToVideo };

if (require.main === module) {
  const args = process.argv.slice(2);
  const options = {};
  for (let i = 0; i < args.length; i += 2) {
    const key = args[i].replace(/^--/, '');
    const val = args[i + 1];
    options[key] = val;
  }

  renderHtmlToVideo({
    inputUrl: options.input,
    outputPath: options.output,
    duration: parseFloat(options.duration || 8),
    fps: parseInt(options.fps || 30),
    width: parseInt(options.width || 1080),
    height: parseInt(options.height || 1920),
    audioPath: options.audio || null
  }).catch(err => {
    console.error(err);
    process.exit(1);
  });
}
