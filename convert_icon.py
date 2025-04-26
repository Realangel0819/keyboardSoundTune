from PIL import Image

# JPG 이미지 열기
img = Image.open('peng.jpg')

# ICO 파일로 저장
img.save('peng.ico', format='ICO') 