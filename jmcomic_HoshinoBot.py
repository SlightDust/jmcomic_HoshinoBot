import asyncio
import jmcomic
from PyPDF2 import PdfReader, PdfWriter
import base64
import os

from hoshino import Service, priv

sv = Service('jmcomic', enable_on_default=False, visible=False, use_priv = priv.NORMAL, manage_priv = priv.SUPERUSER) # SUPERUSER按需修改

_current_path = os.path.dirname(__file__)
config_path = os.path.join(_current_path, 'jm_config.yml')

_pdf_path = "/root/18comic_down/"

def reverse_string(s):
    '''返回字符串s的倒序字符串'''
    return ''.join(reversed(s))

def path2b64(file_path):
    '''
    将本地路径转换为base64字符串
    Args:
      file_path(str): 本地路径
    Returns:
      str: base64字符串
    '''
    with open(file_path, 'rb') as f:
        b64str = base64.b64encode(f.read()).decode()
    return b64str

async def download_comic(comic_id):
    '''异步下载comid_id的漫画，返回True表示下载成功，False表示下载失败
    Returns:
      bool: True表示下载成功，False表示下载失败
      str: 下载成功时返回漫画名称，下载失败时返回错误信息
    '''
    try:
        option = jmcomic.JmOption.from_file(config_path)
        download_task = asyncio.to_thread(jmcomic.download_album,comic_id,option=option)
        task_res = await download_task
        jm_detail, jm_downloader = task_res[0], task_res[1]
        return True, jm_detail.name
    except Exception as e:
        err = f"Error downloading comic: {e}"
        print(err)
        return False, err

def _enctypt_pdf(input_pdf_path, output_pdf_path, password):
    try:
        reader = PdfReader(input_pdf_path)
        writer = PdfWriter()
        for page in reader.pages:
            writer.add_page(page)
        writer.encrypt(password)
        with open(output_pdf_path, "wb") as f:
            writer.write(f)
        return True
    except Exception as e:
        print(f"Error encrypting PDF file: {e}")
        return False

async def encrypt_pdf(input_pdf_path, output_pdf_path, password):
    '''异步加密PDF文件，返回True表示加密成功，False表示加密失败'''
    return await asyncio.to_thread(_enctypt_pdf, input_pdf_path, output_pdf_path, password)

async def llob_cross_host_download_file(bot, b64):
    '''用于llonebot将base64编码的文件下载到本地。
    适用于Hoshino和llonebot不在同一主机或使用了docker的情况。
    因为上传群文件upload_group_file接口不能接受bese64字符串，
    所以先把文件下载到llonebot。
    Returns:
      str: base64编码的文件保存到llonebot本地后的路径
    '''
    downloader = await bot.download_file(base64 = b64)
    return downloader['file']

@sv.on_rex(r'^jm(\d+)$')
async def jmcomic_download(bot, ev):
    comic_id = int(ev.match.group(1))
    await bot.send(ev, f"正在下载JMComic: {comic_id}，请稍候...")
    download_res = await download_comic(comic_id)  # [1]是漫画名称
    if not (download_res[0]):
        await bot.send(ev, "Failed to download comic.")
        return
    if not (await encrypt_pdf(_pdf_path+str(comic_id)+".pdf", _pdf_path+str(comic_id)+"_encrypted.pdf", reverse_string(str(comic_id)))):
        return
    await bot.send(ev, f"uploading...")
    try:
        path = await llob_cross_host_download_file(bot, path2b64(_pdf_path+str(comic_id)+"_encrypted.pdf"))
        await bot.upload_group_file(group_id=ev.group_id, file=path, name=str(comic_id)+".pdf")
    except Exception as e:
        await bot.send(ev, f"上传群文件失败！\n {e}")

# async def main():
#     comic_id = 529481
#     if not ((await download_comic(comic_id))[0]):
#         print("Failed to download comic.")
#         return
#     if not (await encrypt_pdf(_pdf_path+str(comic_id)+".pdf", _pdf_path+str(comic_id)+"_encrypted.pdf", reverse_string(str(comic_id)))):
#         print("Failed to encrypt PDF file.")
#         return
#     print("Done!")
    
# if __name__ == '__main__':
#     asyncio.run(main())