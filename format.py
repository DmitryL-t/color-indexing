from PIL import Image
def to_format_x(img, is_return_rgba, shorten=False):
	from collections import Counter
	h = img.height
	w = img.width
	pixels = img.load()
	mode = img.mode
	if is_return_rgba:
		mode1 = 'RGBA'
	else:
		mode1 = 'RGB'
	s = '\x89CII\r\n\x1a\n'
	c = []
	for i in range(h):
		for j in range(w):
			if mode == mode1 == 'RGB':
				b1 = pixels[j, i]
			elif mode == mode1 == 'RGBA':
				b1 = pixels[j, i]
			elif mode == 'RGB' and mode1 == 'RGBA':
				b1 = pixels[j, i] + [255]
			elif mode == 'RGBA' and mode1 == 'RGB':
				r_, g_, b_, a_ = pixels[j, i]
				r_1 = round(r_ * a_ / 255)
				g_1 = round(g_ * a_ / 255)
				b_1 = round(b_ * a_ / 255)
				b1 = [r_1, g_1, b_1]
			c.append(tuple(b1))
	s1 = 'h = %s, w = %s, mode = %s\n' % (h, w, mode1)
	b = []
	for i in c:
		b += i
	bytes_ = bytes(s, encoding='utf-8') + bytes(s1, encoding='utf-8') + bytes(b)
	n_ = -1
	if shorten:
		counter = Counter(c)
		pixel_size = 3 if mode == 'RGB' else 4
		for s_ in range(1, 8):
			for k in range(0, 10 - s_):
				s1 = 'h = %s, w = %s, mode = %s, i = 1, s = %s, k = %s\n' % (h, w, mode1, s_, k)
				num_colors = (2 ** s_ - 1) * 2 ** k
				colors = counter.most_common(num_colors)
				if len(colors) < num_colors:
					for i in range(num_colors - len(colors)):
						colors.append((tuple([0] * pixel_size), 0))

				colors_ = [i[0] for i in colors]
				common_pixels = 0
				for i in c:
					if i in colors_:
						common_pixels += 1

				num_bytes_x = len(bytes(s, 'utf-8') + bytes(s1, 'utf-8')) + num_colors * pixel_size + (s_ * len(c) + 7) // 8 + (k * common_pixels + 7) // 8 + (len(c) - common_pixels) * pixel_size
				if num_bytes_x > len(bytes_):
					continue

				# Most common colors -> num_colors * pixel_size BYTES
				b1 = []
				for i in colors:
					b1 += i[0]

				# Flag (is color common) -> s_ * len(c) BITS = (s_ * len(c) + 7) // 8 BYTES
				# (s) 0 - non-common color
				# 00101 - common-color [111]
				bits = []
				for i in range(h):
					for j in range(w):
						color = pixels[j, i]
						if color in colors_:
							K = colors_.index(color)
							bits += [int(i) for i in bin(K // 2 ** k + 1)[2:].zfill(s_)]
						else:
							bits += [0] * s_
				while len(bits) % 8 != 0:
					bits.append(0)
				b2 = []
				for i in range(len(bits) // 8):
					b2 += [int(''.join([str(i) for i in bits[8 * i:8 * i + 8]]), 2)]
				
				# Common colors value -> k * common_pixels BITS = (k * common_pixels + 7) // 8 BYTES
				bits = []
				for i in range(h):
					for j in range(w):
						color = pixels[j, i]
						if color in colors_:							
							K1 = colors_.index(color)
							if k > 0:
								bits += [int(i) for i in bin(K1 % 2 ** k)[2:].zfill(k)]

						else:
							bits += [0] * k

				while len(bits) % 8 != 0:
					bits.append(0)
				b3 = []
				for i in range(len(bits) // 8):
					b3 += [int(''.join([str(i) for i in bits[8 * i:8 * i + 8]]), 2)]

				# Non-common colors -> (len(c) - common_pixels) * pixel_size BYTES
				b4 = []
				for i in c:
					if i not in colors_:
						b4 += list(i)

				bytes1 = bytes(s, encoding='utf-8') + bytes(s1, encoding='utf-8') + bytes(b1 + b2 + b3 + b4)
				if len(bytes1) < len(bytes_):
					bytes_ = bytes1
	return bytes_

def to_pixels(bytes_):
	if not bytes_.startswith(b'\xc2\x89CII\r\n\x1a\n'):
		return None
	bytes_ = bytes_[9:]
	s1 = bytes_.split(b'\n')[0]
	bytes_ = b'\n'.join(bytes_.split(b'\n')[1:])
	d = s1.decode('utf-8').split(',')
	dict_ = {}
	for i in d:
		l = [j.strip() for j in i.split('=')]
		if len(l) != 2:
			return None
		key, val = l
		dict_[key] = val
	h = dict_.get('h')
	if h == None:
		h = 1080
	elif len(h) > 0 and sum([1 if '0' <= i <= '9' else 0 for i in h]) == len(h):
		h = int(h)
	else:
		h = 1080
	w = dict_.get('w')
	if w == None:
		w = 1080
	elif len(w) > 0 and sum([1 if '0' <= i <= '9' else 0 for i in w]) == len(w):
		w = int(w)
	else:
		w = 1080
	mode = dict_.get('mode', 'RGB')
	if mode not in ('RGB', 'RGBA'):
		return None
	i_ = dict_.get('i')
	if i_ == '1' or i_ == 'True':
		shorten = True
	else:
		shorten = False

	s_ = dict_.get('s', '3')
	if len(s_) > 0 and sum([1 if '0' <= i <= '9' else 0 for i in s_]) == len(s_):
		s_ = int(s_)
	else:
		s_ = None

	k = dict_.get('k', '3')
	if len(k) > 0 and sum([1 if '0' <= i <= '9' else 0 for i in k]) == len(k):
		k = int(k)
	else:
		k = None

	default_color = (0, 0, 0) if mode == 'RGB' else (0, 0, 0, 255)
	pixel_size = 3 if mode == 'RGB' else 4
	# (s, k)
	# s bits - 000... - non-common, ...1... - common
	# k bits - only for common

	if i == -1:
		pixels = [[default_color] * w for i in range(h)]
		for i in range(len(s1) // pixel_size):
			h1, w1 = i // w, i % w
			if h1 < h:
				pixels[h1][w1] = tuple(s1[pixel_size * i:pixel_size * i + pixel_size])
	else:
		if s_ == None or k == None:
			return None
		num_colors = (2 ** s_ - 1) * 2 ** k
		common_colors = []
		if len(bytes_) < num_colors * pixel_size:
			return False
		
		# b1
		for i in range(num_colors):
			common_colors.append(tuple(bytes_[i * pixel_size:i * pixel_size + pixel_size]))
		bytes_ = bytes_[num_colors * pixel_size:]
		bits = []
		for i in bytes_:
			bits += [int(_) for _ in bin(i)[2:].zfill(8)]
		pixels = [[None] * w for i in range(h)]
		for i in range(w * h):
			pixels[i // w][i % w] = int(''.join([str(_) for _ in bits[s_ * i:s_ * i + s_]]), 2)
		
		bits = bits[w * h * s_:]
		if len(bits) % 8 != 0:
			bits = bits[len(bits) % 8:]

		L = 0
		for i in range(h):
			for j in range(w):
				if pixels[i][j] == 0:
					L += 1

		zero_list = []
		non_zero_list = []
		for i in range(h):
			for j in range(w):
				if pixels[i][j] == 0:
					zero_list.append((i, j))
				else:
					non_zero_list.append((i, j))

		for i in range(h * w - L):
			index = non_zero_list[i]
			a = pixels[index[0]][index[1]]
			b = int('0' + ''.join([str(_) for _ in bits[i * k:i * k + k]]), 2)
			color_index = (a - 1) * 2 ** k + b
			pixels[index[0]][index[1]] = common_colors[color_index]

		bits = bits[(h * w - L) * k:]
		if len(bits) % 8 != 0:
			bits = bits[len(bits) % 8:]

		bytes_ = []
		for i in range(len(bits) // 8):
			bytes_.append(int(''.join([str(_) for _ in bits[8 * i:8 * i + 8]]), 2))

		for i in range(L):
			index = zero_list[i]
			pixels[index[0]][index[1]] = tuple(bytes_[pixel_size * i:pixel_size * i + pixel_size])

	return (h, w, mode, pixels)

path = 'demo.png'
img = Image.open(path)
pixels1 = img.load()
f = to_format_x(img, True, True)
image = to_pixels(f)
height, width, mode, pixels2 = image
print(img.height, height)
print(img.width, width)
print(img.mode, mode)
for i in range(height):
	for j in range(width):
		try:
			if pixels1[j, i] != pixels2[i][j]:
				print((j, i))
		except:
			pass
