from PIL import Image

txt = open("/home/imperator/CTF/CYBERSPACE/empty.txt", "r").readline()
n = int(len(txt) ** .5)

img = Image.new('RGB', (n, n), (255,) * 3)
img.putdata([(255 * (c == " "),) * 3 for c in txt])
img.show()
