import cv2, numpy as np, sys
from bg1 import floor_model
n=sys.argv[1]
im=cv2.imread(n+".jpg"); big=cv2.imread(n+"_big.png",0)
ker=lambda r: cv2.getStructuringElement(cv2.MORPH_ELLIPSE,(2*r+1,2*r+1))
inp=cv2.inpaint(im, cv2.dilate(big,ker(6)), 6, cv2.INPAINT_TELEA)
B=floor_model(inp)
L=cv2.cvtColor(im,cv2.COLOR_BGR2GRAY).astype(np.float32)
BL=cv2.cvtColor(np.clip(B,0,255).astype(np.uint8),cv2.COLOR_BGR2GRAY).astype(np.float32)
R=L/np.maximum(BL,1)
np.save(n+"_R.npy",R); cv2.imwrite(n+"_B2.png",np.clip(B,0,255).astype(np.uint8)); cv2.imwrite(n+"_inp.png",inp)
M=((R<0.96)&(R>0.62)&(big==0)).astype(np.uint8)*255
lines=cv2.HoughLinesP(M,1,np.pi/720,threshold=120,minLineLength=220,maxLineGap=25)
out=cv2.cvtColor(np.clip((R-0.5)*255,0,255).astype(np.uint8),cv2.COLOR_GRAY2BGR)
if lines is not None:
    for l in lines.reshape(-1,4):
        x1,y1,x2,y2=l; print(l); cv2.line(out,(x1,y1),(x2,y2),(0,0,255),2)
cv2.imwrite(n+"_hough.png",out)
