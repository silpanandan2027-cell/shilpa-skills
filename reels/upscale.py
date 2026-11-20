"""Upscale a 2K still to at least a 2160x3840 frame: FSRCNN x2 super-resolution, then a gentle unsharp mask.

Usage: python3 upscale.py model.pb in.png out.png
"""
import sys
import cv2

model, src, dst = sys.argv[1:4]
img = cv2.imread(src)
if img.shape[1] < 2160:
    sr = cv2.dnn_superres.DnnSuperResImpl_create()
    sr.readModel(model)
    sr.setModel("fsrcnn", 2)
    img = sr.upsample(img)
    blur = cv2.GaussianBlur(img, (0, 0), 1.2)
    img = cv2.addWeighted(img, 1.35, blur, -0.35, 0)
cv2.imwrite(dst, img)
print(dst, img.shape[1], "x", img.shape[0])
