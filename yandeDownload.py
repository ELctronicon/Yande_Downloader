import os
import requests
from bs4 import BeautifulSoup
import time
import random
from PIL import Image
import io
import re
import urllib
from fake_useragent import UserAgent


class YandeDownloader:
	def __init__(self):
		# self.user_agents = [UserAgent().random for _ in range(10)]
		self.user_agents = [
			'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/98.0.4758.102 Safari/537.36',
			'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/88.0.4324.182 Safari/537.36',
			'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Firefox/97.0',
			'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Edge/98.0.1108.43',
			'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Safari/537.36',
		]
		self.page_size = 40
		self.save_folder = r".\images" # Directory where images will be saved
		self.max_name_length = 210  # File path name length limit on Windows
		self.site_name = "yande.re"
		self.tag_list = []
		self.pid_start, self.pid_end = 0, 0
		self.current_page = 0
		self.error_url = []

		# If tags for the corresponding images are needed, the images can be saved to a CSV file later
		# key=file_path and value=tag
		self.save_tags = {}

	def get_image_tags(self, url: str) -> tuple:
		"""
		Extracts tags from the given image URL.

		Parameters:
			url (str): The URL of the image.

		Returns:
			str: A formatted string of tags for the image.
		"""
		name = url.split('/')[-1]
		tags = urllib.parse.unquote(name).split(' ')
		save_name, tags_list = "-".join(tags[1:]), tags[2:]
		return save_name, tags_list

	def set_download_params(self):
		"""
		Sets the tags and the range of pages to download.
		"""
		self.tag_list = self.get_tags()
		self.pid_start, self.pid_end = self.get_page_range()
		self.current_page = self.pid_start // self.page_size + 1

	def set_download_auto(self, tags: list, pages: list or int):
		"""
		Sets the tags and the range of pages for automatic downloading.

		Parameters:
			tags (list): List of tags to search for.
			pages (list or int): Range of pages to download or a single page number.
		"""
		self.tag_list = self.get_tags(tags)
		self.pid_start, self.pid_end = self.get_page_range(pages)
		self.current_page = self.pid_start // self.page_size + 1

	def get_tags(self, tags: list = 0) -> list:
		"""
		Prompts the user for tags to download.

		Parameters:
			tags (list, optional): Predefined list of tags.

		Returns:
			list: List of tags to download.
		"""
		if not tags:
			tags = input("Enter Tags: ").split()
		print(f"|| Searching tags: {tags} ||")
		return tags

	def get_page_range(self, pages: list or int = 0) -> tuple:
		"""
		Prompts the user for page range and calculates start and end pids.

		Parameters:
			pages (list or int, optional): Range of pages to download or a single page number.

		Returns:
			tuple: A tuple containing the start and end page IDs.
		"""
		if not pages:
			pages = list(map(int, input("Enter pages to download (e.g., '1 3' for page 1 to 3): ").split()))
		if isinstance(pages, list) and len(pages) == 1:
			pages.append(pages[0])
		elif isinstance(pages, int):
			pages = [pages, pages]
		start = max(pages[0], 1)
		end = max(pages[1], start)
		pid_start = (start - 1) * self.page_size
		pid_end = end * self.page_size
		return pid_start, pid_end

	def headers(self) -> dict:
		"""
		Randomizes the User-Agent to avoid detection.

		Returns:
			dict: A dictionary containing the randomized User-Agent header.
		"""
		return {'User-Agent': random.choice(self.user_agents)}

	def request_page(self, url: str, max_attempts: int = 5) -> str:
		"""
		Attempts to fetch the page content with retry logic.

		Parameters:
			url (str): The URL of the page to fetch.
			max_attempts (int): Maximum number of retry attempts.

		Returns:
			str: The HTML content of the page or None if failed.
		"""
		for attempt in range(max_attempts):
			try:
				response = requests.get(url, headers=self.headers())
				response.raise_for_status()
				return response.text
			except requests.RequestException as e:
				print(f"Error fetching {url}: {e}. Retrying {attempt + 1}/{max_attempts}")
				time.sleep(5)
		return None

	def fetch_image_links(self, page_html: str) -> list:
		"""
		Extracts image links from the page.

		Parameters:
			page_html (str): The HTML content of the page.

		Returns:
			list: List of image link elements found on the page.
		"""
		soup = BeautifulSoup(page_html, 'html.parser')
		return soup.findAll('a', {'class': "directlink largeimg"})

	def download_image(self, url: str) -> bytes:
		"""
		Downloads and saves an image from the given URL.

		Parameters:
			url (str): The URL of the image to download.

		Returns:
			bytes: The content of the downloaded image or None if failed.
		"""
		max_attempts = 5
		for attempt in range(max_attempts):
			try:
				response = requests.get(url, headers=self.headers())
				response.raise_for_status()
				image = Image.open(io.BytesIO(response.content))
				image.verify()  # Verify that it is an actual image
				return response.content
			except Exception as e:
				print(f"|| Failed to download image: {e} Retrying {attempt}/{max_attempts}||")
		return None

	def get_save_filename(self, img_url: str) -> str:
		"""
		Constructs the save filename based on the image URL and tags.

		Parameters:
			img_url (str): The URL of the image.

		Returns:
			str: The full path to save the image.
		"""
		tag_dir = '+'.join(self.tag_list) or "all"
		save_path = os.path.join(self.save_folder, self.site_name, tag_dir)
		os.makedirs(save_path, exist_ok=True)
		save_name, tags_list = self.get_image_tags(img_url)

		file_name = os.path.join(save_path, save_name)
		if len(file_name) > self.max_name_length:
			file_name = os.path.join(save_path, save_name[len(file_name) - self.max_name_length])
		self.save_tags[file_name] = tags_list
		return file_name

	def save_image(self, img_url: str, img_data: bytes) -> bool:
		"""

		Saves the downloaded image to the appropriate directory.

		Parameters:
			img_url (str): The URL of the image.
			img_data (bytes): The content of the image to save.

		Returns:
			bool: True if the image was saved successfully, False otherwise.
		"""
		file_name = self.get_save_filename(img_url)
		try:
			with open(file_name, 'wb') as file:
				file.write(img_data)
			return True
		except Exception as e:
			print(f"Error saving {file_name}: {e}")
			return False

	def download_images_from_page(self, page_url: str):
		"""
		Downloads all images from a page.

		Parameters:
			page_url (str): The URL of the page to download images from.
		"""
		page_html = self.request_page(page_url)
		if not page_html:
			return

		image_links = self.fetch_image_links(page_html)
		if not image_links:
			print("|| The Page is Empty ||")
		for link in image_links:
			img_url = link['href']
			if os.path.exists(self.get_save_filename(img_url)):
				print(f"|| File Exist : {img_url} ||")
				continue
			img_data = self.download_image(img_url)
			if img_data:
				self.save_image(img_url, img_data)
				print(f"|| Download Success : {img_url} ||")
			else:
				self.error_url.append(img_url)
				print(f"|| Download Error : {img_url} ||")

	def build_page_url(self) -> str:
		"""
		Constructs the URL to a specific page.

		Returns:
			str: The constructed page URL.
		"""
		return f"https://{self.site_name}/post?page={self.current_page}&tags={'+'.join(self.tag_list)}"

	def start_download(self):
		"""
		Main function to initiate the download process for each page.
		"""
		while self.pid_start < self.pid_end:
			page_url = self.build_page_url()
			print(f"|| Downloading images from Page: {self.current_page} | page_url: {page_url} ||")
			self.download_images_from_page(page_url)

			self.current_page += 1
			self.pid_start += self.page_size

	def main(self):
		self.set_download_params()
		while True:
			self.start_download()
			if input("Enter [c] to continue with different tags/pages, or any other key to exit: ").lower() != 'c':
				break
			os.system('cls')
			self.set_download_params()

	def auto_main(self, tags: list, pages: list):
		for tag in tags:
			for page in pages:
				print(f"|| Now Downloading | Tags: {tag} | Images Pages start: {pages[0]} | end: {pages[1]} ||")
				self.set_download_auto(tag, page)
				self.start_download()


if __name__ == '__main__':
	# arknights = [["nian_(arknights)"], ["ling_(arknights)"], ["dusk_(arknights)"], ["goldenglow_(arknights)"],
	# 			 ["degenbrecher_(arknights)"], ["amiya_(arknights)"], ["la_pluma_(arknights)"], ["specter_(arknights)"],
	# 			 ["skadi_(arknights)"], ["siege_(arknights)"], ["lappland_(arknights)"], ["texas_(arknights)"],
	# 			 ["kal'tsit_(arknights)"], ["naked", "arknights"]]
	genshin_impact = [["yelan"], ["raiden_shogun"], ["ganyu"], ["kamisato_ayaka"], ["lumine"], ["yae_miko"],
					  ["jean_(genshin_impact)"], ["barbara_(genshin_impact)"], ["arlecchino"],
					  ["lisa_(genshin_impact)"], ["mona_megistus"], ["shenhe"], ["firefly"],
					  ["lynette_(genshin_impact)"],["furina"],["clorinde"]]
	pages = [[1, 15]]
	# pages = [1, 2, 4, 6]
	H = YandeDownloader()
	# H.main()
	H.auto_main(genshin_impact, pages)
