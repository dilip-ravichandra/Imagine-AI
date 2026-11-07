"""Synthetic test images only (no copyrighted or real photos)."""
import numpy as np


def gradient(h=64, w=96):
    x = np.linspace(0, 255, w, dtype=np.float32)[None, :].repeat(h, 0)
    y = np.linspace(0, 255, h, dtype=np.float32)[:, None].repeat(w, 1)
    return np.stack([x, y, (x + y) / 2], axis=-1).astype(np.uint8)


def step(h=64, w=64, lo=76, hi=178):
    im = np.zeros((h, w, 3), np.uint8)
    im[:, : w // 2], im[:, w // 2:] = lo, hi
    return im


def noisy(im, sigma=8.0, seed=0):
    rng = np.random.default_rng(seed)
    return np.clip(im.astype(np.float64) + rng.normal(0, sigma, im.shape), 0, 255).astype(np.uint8)


def checker(n=64, cell=1):
    yy, xx = np.indices((n, n))
    v = (((yy // cell) + (xx // cell)) % 2 * 255).astype(np.uint8)
    return np.stack([v, v, v], -1)


def luma(im):
    return (0.299 * im[..., 0] + 0.587 * im[..., 1] + 0.114 * im[..., 2]).astype(np.float64)


def scene(n=384):
    """Clean synthetic scene with edges, gradients and a thin line (coordinates scale with n)."""
    import cv2
    k = n / 384.0
    yy, xx = np.mgrid[0:n, 0:n].astype(np.float32)
    img = np.zeros((n, n, 3), np.float32)
    img[..., 0], img[..., 1], img[..., 2] = 120 + 0.25 * yy / k, 170 - 0.15 * yy / k, 220 - 0.3 * yy / k
    cv2.circle(img, (int(130 * k), int(150 * k)), int(70 * k), (230, 60, 50), -1)
    cv2.rectangle(img, (int(220 * k), int(190 * k)), (int(340 * k), int(320 * k)), (40, 160, 70), -1)
    cv2.line(img, (0, int(330 * k)), (n, int(300 * k)), (240, 240, 240), max(1, int(6 * k)))
    return np.clip(img, 0, 255).astype(np.uint8)


def blur(a, sigma):
    import cv2
    return cv2.GaussianBlur(a, (0, 0), sigma)


def darker(a, f):
    return np.clip(a.astype(np.float32) * f, 0, 255).astype(np.uint8)
