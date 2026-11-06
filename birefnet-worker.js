import { BackgroundRemover } from 'https://esm.sh/@katana-video/web-bg-removal@0.1.1?bundle';

let remover = null;

self.onmessage = async (event) => {
  const { file, requestId } = event.data || {};
  let bitmap = null;
  let cutout = null;

  try {
    if (!file || !Number.isInteger(requestId)) {
      throw new Error('Permintaan pemrosesan tidak valid.');
    }

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
      label: 'Model siap · menganalisis objek…'
    });

    bitmap = await createImageBitmap(file);
    cutout = await remover.removeBackground(bitmap);

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
