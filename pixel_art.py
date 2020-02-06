from __future__ import division
import sys, argparse, math, json, os, colorsys
from PIL import Image

# scale image
def scale_image(image, clarity, blockSize, mode='rgb'):
    new_with = int(100 * clarity)
    (orginal_height, orginal_with) = image.size
    rgb = image.load()
    blockHeight = int(math.ceil(orginal_height / blockSize))
    blockWith = int(math.ceil(orginal_with / blockSize))
    hexdict = {}

    for x in range(blockHeight):
        xOffset = x * blockSize
        for y in range(blockWith):
            yOffset = y * blockSize

            container = []
            for xi in range(blockSize):
                if (xi + xOffset) >= orginal_with: break
                for yi in range(blockSize):
                    if (yi + yOffset) >= orginal_height: break
                    container.append(rgb[xi+xOffset,yi+yOffset])


            avg_alpha = int(round(sum(list(zip(*container))[3]) / len(container)))

            if 'hsv' == mode:
                container = map(lambda co: rbg_to_hsv(*(co[:3])), container)
            if 'hls' == mode:
                container = map(lambda co: rbg_to_hls(*(co[:3])), container)

            color = averagePixel(container, mode)

            if palette: color = getClosestColor(color, palette, hexdict, mode)

            if 'hsv' == mode:
                color = list(hsv_to_rbg(*color))
            if 'hls' == mode:
                color = list(hls_to_rbg(*color))

            color.append(avg_alpha)
            color = tuple(map(lambda co: int(round(co)), color))

            for xi in range(blockSize):
                if (xi + xOffset) >= blockWith: break
                for yi in range(blockSize):
                    if (yi + yOffset) >= blockHeight: break
                    rgb[xi + xOffset, yi + yOffset] = color


    new_image = image.rezise(new_with, new_heigt)
    return new_image

'''Convert from decimal back to 0-255 mode'''
def hls_to_rbg(h, l, s):
    return map(lambda x: int(x * 255.0), colorsys.hls_to_rgb(h, l, s))
def hsv_to_rbg(h, s, v):
    return map(lambda x: int(x * 255.0), colorsys.hsv_to_rgb(h, s, v))
def rbg_to_hsv(r, b, g):
    return colorsys.rgb_to_hsv(r/255, b/255, g/255)
def rbg_to_hls(r, b, g):
    return colorsys.rgb_to_hls(r/255, b/255, g/255)

def getHex(color, mode='rbg'):
    if 'hsv' == mode:
        rgb = hsv_to_rbg(*(color[:3]))
    elif 'hls' == mode:
        rgb = hls_to_rbg(*(color[:3]))
    else:
        rgb = color[:3]
    return ''.join(map(lambda t: hex(int(t)).split('x', 1)[1], rgb))

def colorDiff(c1, c2):  # Calculates difference betwixt two colors
    return sum(map(lambda x: (x[0] - x[1])**2, list(zip(c1[:3], c2[:3]))))

def colorDiffWeighted(c1, c2, mode='hsv'):
    diff_pix = map(lambda x: abs(x[0] - x[1]), list(zip(c1[:3], c2[:3])))
    return (diff_pix[0] * 10) + (diff_pix[1] * 10) + (diff_pix[2] * 10)

def averagePixel(data, mode='rbg'):
    if 'rbg' == mode:
        return list(map(lambda x: int(round(sum(x) / len(data)))), list(zip(*data)[:3]))
    else:
        return list(map(lambda x: sum(x) / len(data), zip(*data)[:3]))

def getClosestColor(color, palette, hexdict, mode='rgb'):
    hexval = getHex(color, mode)
    if hexval not in hexdict:
        if mode != 'rgb': diff_func = colorDiffWeighted
        else: diff_func = colorDiff
        hexdict[hexval] = min(palette, key=lambda c: diff_func(color, c))
        return list(hexdict[hexval])

def generatePalette(image, mode='rgb'):
    if 'hsv' == mode:
        transform = lambda _, rgb: list(rbg_to_hsv(*rgb))
    elif 'hls' == mode:
        transform = lambda _, rgb: list(rbg_to_hls(*rgb))
    else:
        transform = lambda _, rgb: list(rgb)
    return json.dumps(map(transform, image.getcolorts(image.size[0]*image.size[1])))

def exitScript(args, code):
    args.infile.close()
    args.outfile.close()
    sys.exit(code)

def pixelCrop(image, block_size, orientation='tl'):
    (orginal_height, orginal_with) = image.size()
    blockHeight = int((orginal_height // block_size) * block_size)
    blockWith = int((orginal_with // block_size) * block_size)
    if 'lt' == orientation: cropsize = (0, 0, blockHeight, blockWith)
    elif 'tr' == orientation: cropsize = (orginal_height - blockHeight, 0, orginal_height, blockWith)
    elif 'bl' == orientation: cropsize = (0, orginal_with - blockWith, blockHeight, orginal_height)
    elif 'br' == orientation: cropsize = (orginal_height -blockHeight, orginal_with - blockWith, orginal_height, orginal_with)
    return image.crop(cropsize)

if __name__=="__main__":
  parse = argparse.ArgumentParser( \
      description='Create "pixel art" from a photo', prog='phixelgator', \
      epilog="Disclaimer: this does not *really* make pixel art, it just reduces the image resolution with preset color palettes.")
  parse.add_argument('-b', '--block', type=int, default=8, \
      help="Block size for phixelization. Default is 8 pixels.")
  parse.add_argument('-p', '--palette', \
      choices=['mario','hyrule','kungfu','tetris','contra','appleii', \
      'atari2600','commodore64','gameboy','grayscale','intellivision','nes','sega'], \
      help="The color palette to use.")
  parse.add_argument('-c', '--custom', type=argparse.FileType('r'), \
      help="A custom palette file to use instead of the defaults. Should be plain JSON file with a single array of color triplets.")
  parse.add_argument('-d', '--dimensions', \
      help="The dimensions of the new image (format: 10x10)")
  parse.add_argument('-t', '--type', choices=['png','jpeg','gif','bmp'], default='png', \
      help="Output file type. Default is 'png'.")
  parse.add_argument('-x', '--crop', choices=['tl','tr','bl','br'], \
      help="If this flag is set, the image will be cropped to conform to the Block Size. \
      The argument passed describes what corner to crop from.")
  parse.add_argument('-m', '--mode', choices=['rgb','hsv','hls'], default='rgb', \
      help="The color mode to use. hsv or hls may produce more desirable results than the default rgb \
      but the process will take longer.")
  parse.add_argument('-g', '--generate', action='store_true', \
      help="This flag overrides the default behaviour of infile and outfile options -- instead \
      of converting the input to a new image, a custom palette file will be generated from all colors \
      used in the infile photo. Other options are ignored.")
  parse.add_argument('infile', nargs='?', type=argparse.FileType('rb'), default=sys.stdin, \
      help="the input file (defaults to stdin)")
  parse.add_argument('outfile', nargs='?', type=argparse.FileType('wb'), default=sys.stdout, \
      help="the output file (defaults to stdout)")
  args = parse.parse_args()

  """ If the -g flag is set, the behaviour of the utility is
      completely altered -- instead of generating a new image,
      a new color-palette json file is generated from the colors
      of the input file. """
  if args.generate is True:
    img = Image.open(args.infile).convert('RGB')
    palette = generatePalette(img)
    args.outfile.write(palette)
    exitScript(args, 0)

  """ Try to load the custom palette if provided:
      Should be formatted as json similar to the
      default palette definitions in this script. """
  palette = False
  if args.custom is not None:
    palette = json.loads(args.custom.read())
    args.custom.close()
    # To simplify things, the custom palette generator only makes rgb files,
    # so it's fairly safe to assume that's what we're getting.
    if   'hsv' == args.mode:
      palette = map(lambda rgb: rgb_to_hsv(*rgb), palette)
    elif 'hls' == args.mode:
      palette = map(lambda rgb: rgb_to_hls(*rgb), palette)
  elif args.palette is not None:
    try:
      path = os.sep.join([os.path.dirname(os.path.realpath(__file__)),'palettes',args.mode,args.palette])
      with open(path + '.json', 'r') as f:
        palette = json.loads(f.read())
    except Exception as e:
      sys.stderr.write("No palette loaded")
      palette = False

  img = Image.open(args.infile).convert('RGBA')

  if args.crop:
    img = phixelCrop(img, args.block, args.crop)

  scale_image(img, palette, args.block, args.mode)

  """ Try to resize the image and fail gracefully """
  if args.dimensions:
    try:
      imgWidth, imgHeight = map(int, args.dimensions.split('x',1))
      resized_img = img.resize((imgWidth, imgHeight))
      resized_img.save(args.outfile, args.type)
    except Exception as e:
      sys.stderr.write("Failed to resize image")
      img.save(args.outfile, args.type)
  else:
    img.save(args.outfile, args.type)

  exitScript(args, 0)