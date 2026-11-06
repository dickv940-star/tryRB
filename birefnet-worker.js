import { BackgroundRemover } from 'https://esm.sh/@katana-video/web-bg-removal@0.1.1?bundle';

let remover = null;

function gpuUnavailable(error) {
  return /webgpu|webgl|context provider|no available adapters|gpu backend/i.test(
    error?.message || String(error)
  );
}

async function removeWithCpuFallback(file, requestId, originalBitmap, primaryError) {
  self.postMessage({
    type: 'stage',
    requestId,
    label: 'GPU tidak tersedia · beralih ke AI CPU/WASM…'
  });

  const module = await import('https://esm.sh/@imgly/background-removal@1.7.0?bundle');
  const removeBackground = module.default;
  if (typeof removeBackground !== 'function') {
    throw new Error('Mesin cadangan CPU/WASM gagal dimuat.');
  }

  const blob = await removeBackground(file, {
    device: 'cpu',
    model: 'isnet_quint8',
    debug: false,
    output: {
      format: 'image/png',
      type: 'foreground'
    }
  });

  if (!blob || blob.type !== 'image/png') {
    throw new Error('Mesin cadangan CPU/WASM tidak menghasilkan PNG transparan.');
  }

  const check = await createImageBitmap(blob);
  const validSize = check.width === originalBitmap.width &&
    check.height === originalBitmap.height;
  check.close();

  if (!validSize) {
    throw new Error('Mesin cadangan mengubah dimensi foto. Hasil dibatalkan.');
  }

  self.postMessage({
    type: 'done',
    requestId,
    blob,
    width: originalBitmap.width,
    height: originalBitmap.height,
    backend: 'ISNet CPU/WASM',
    dtype: 'quint8'
  });
}

self.onmessage = async (event) => {
  const { file, requestId } = event.data || {};
  let bitmap = null;
  let cutout = null;

  try {
    if (!file || !Number.isInteger(requestId)) {
      throw new Error('Permintaan pemrosesan tidak valid.');
    }

    bitmap = await createImageBitmap(file);

    try {
      if (!remover) {
        remover = await BackgroundRemover.load('birefnet_lite', {
          backend: 'auto',
          dtype: 'auto',
          onProgress: (fraction) => self.postMessage({
            type: 'progress',
            requestId,
            value: fraction
          })
        });
      }

      self.postMessage({
        type: 'stage',
        requestId,
        label: 'Model BiRefNet siap · menganalisis objek…'
      });

      cutout = await remover.removeBackground(bitmap);
    } catch (primaryError) {
      if (!gpuUnavailable(primaryError)) throw primaryError;
      await removeWithCpuFallback(file, requestId, bitmap, primaryError);
      return;
    }

    if (cutout.width !== bitmap.width || cutout.height !== bitmap.height) {
      throw new Error('Model mengubah dimensi gambar; hasil dibatalkan.');
    }

    const canvas = new OffscreenCanvas(cutout.width, cutout.height);
    const context = canvas.getContext('2d', { alpha: true });
    if (!context) throw new Error('Browser tidak dapat membuat kanvas transparan.');

    context.clearRect(0, 0, cutout.width, cutout.height);
    context.drawImage(cutout, 0, 0);

    const blob = await canvas.convertToBlob({ type: 'image/png' });
    if (!blob || blob.type !== 'image/png') {
      throw new Error('Browser gagal menghasilkan PNG transparan.');
    }

    self.postMessage({
      type: 'done',
      requestId,
      blob,
      width: cutout.width,
      height: cutout.height,
      backend: remover.backend,
      dtype: remover.dtype
    });
  } catch (error) {
    self.postMessage({
      type: 'error',
      requestId,
      message: error?.message || String(error)
    });
  } finally {
    bitmap?.close();
    cutout?.close();
  }
};
