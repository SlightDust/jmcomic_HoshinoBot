import asyncio
import jmcomic
from PyPDF2 import PdfReader, PdfWriter
import base64
import os
import yaml
import pyzipper

from hoshino import Service, priv

sv = Service('jmcomic', enable_on_default=False, visible=False, use_priv = priv.NORMAL, manage_priv = priv.SUPERUSER) # SUPERUSER按需修改

_current_path = os.path.dirname(__file__)
config_path = os.path.join(_current_path, 'jm_config.yml')

UPLOAD_FILE_TYPE = 3
'''
1: 未加密PDF（相思了？）
2: 加密PDF
3: 加密zip，里面是未加密PDF (recommended)
4. 加密zip，里面是加密PDF
'''

assert UPLOAD_FILE_TYPE in [1, 2, 3, 4], "UPLOAD_FILE_TYPE must be 1, 2, 3 or 4"

downloading_queue = []

def read_pdf_dir_config(config_path):
    '''从jmcomic配置文件里读取pdf_dir路径'''
    with open(config_path, 'r', encoding='utf-8') as file:
        config = yaml.safe_load(file)
    
    pdf_dir = config.get('plugins', {}).get('after_album', [{}])[0].get('kwargs', {}).get('pdf_dir')
    return pdf_dir

_output_path = read_pdf_dir_config(config_path)


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

def _encrypt_zip(input_file_path, output_pdf_path, password):
    zip = pyzipper.AESZipFile(output_pdf_path, "w", compression=pyzipper.ZIP_DEFLATED, encryption=pyzipper.WZ_AES)  
    # win10资源管理器不能解压AES加密的压缩文件，得用7zip之类的
    try:
        zip.setpassword(password.encode("utf-8"))
        zip.write(input_file_path, os.path.basename(input_file_path), compress_type=pyzipper.ZIP_DEFLATED)
        zip.close()
        return True
    except Exception as e:
        zip.close()
        print(f"Error encrypting zip file: {e}")
        return False

async def encrypt_zip(input_file_path, output_pdf_path, password):
    '''异步加密zip文件，返回True表示加密成功，False表示加密失败'''
    return await asyncio.to_thread(_encrypt_zip, input_file_path, output_pdf_path, password)

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

async def is_exist_comic(comic_id):
    '''判断漫画是否存在
    Returns:
      bool: True表示漫画存在，False表示漫画不存在
    '''
    if UPLOAD_FILE_TYPE == 1:
        return os.path.exists(_output_path+str(comic_id)+".pdf")
    elif UPLOAD_FILE_TYPE == 2:
        return os.path.exists(_output_path+str(comic_id)+"_encrypted.pdf")
    elif UPLOAD_FILE_TYPE == 3:
        return os.path.exists(_output_path+str(comic_id)+".zip")
    elif UPLOAD_FILE_TYPE == 4:
        return os.path.exists(_output_path+str(comic_id)+"_encrypted.zip")

async def do_upload(bot, ev, comic_id):
    '''上传文件到'''
    if UPLOAD_FILE_TYPE == 1:
        file_path = _output_path+str(comic_id)+".pdf"
    elif UPLOAD_FILE_TYPE == 2:
        file_path = _output_path+str(comic_id)+"_encrypted.pdf"
    elif UPLOAD_FILE_TYPE == 3:
        file_path = _output_path+str(comic_id)+".zip"
    elif UPLOAD_FILE_TYPE == 4:
        file_path = _output_path+str(comic_id)+"_encrypted.zip"
    try:
        path = await llob_cross_host_download_file(bot, path2b64(file_path))
        await bot.upload_group_file(group_id=ev.group_id, file=path, name=os.path.basename(file_path))
    except Exception as e:
        await bot.send(ev, f"上传群文件失败！\n {e}")

async def process_file(comic_id):
    '''根据UPLOAD_FILE_TYPE 处理文件
    Args:
        comic_id: str jmid
    Returns:
        bool: True表示处理成功，False表示处理失败
        str: 处理成功时返回空字符串，处理失败时返回错误信息
    '''
    pure_pdf = _output_path+str(comic_id)+".pdf"
    enc_pdf = _output_path+str(comic_id)+"_encrypted.pdf"
    enc_zip_n_pure_pdf = _output_path+str(comic_id)+".zip"
    enc_zip_n_enc_pdf = _output_path+str(comic_id)+"_encrypted.zip"
    pwd = reverse_string(str(comic_id))

    if UPLOAD_FILE_TYPE == 1: 
        return True, ""
    if UPLOAD_FILE_TYPE in [2, 4]:
        if not (await encrypt_pdf(pure_pdf, enc_pdf, pwd)):
            msg = f"{comic_id}加密PDF文件失败"
            return False, msg
        if UPLOAD_FILE_TYPE == 2:
            return True, ""
        elif UPLOAD_FILE_TYPE == 4:
            if not (await encrypt_zip(enc_pdf, enc_zip_n_enc_pdf, pwd)):
                msg = f"{comic_id}加密zip文件失败(with encrypted pdf)"
                return False, msg
            return True, ""
    if UPLOAD_FILE_TYPE == 3:
        if not (await encrypt_zip(pure_pdf, enc_zip_n_pure_pdf, pwd)):
            msg = f"{comic_id}加密zip文件失败(with pure pdf)"
            return False, msg
        return True, ""
        
@sv.on_rex(r'^jm(\d+)$')
async def jmcomic_download(bot, ev):
    comic_id = int(ev.match.group(1))
    if await is_exist_comic(comic_id):
        await bot.send(ev, f"JMComic: {comic_id}已存在，正在上传...")
        await do_upload(bot, ev, comic_id)
        return
    if comic_id in downloading_queue:
        await bot.send(ev, f"{comic_id}已被提交下载，请稍后再试...")
        return
    await bot.send(ev, f"正在下载JMComic: {comic_id}，请稍候...")
    downloading_queue.append(comic_id)
    download_res = await download_comic(comic_id)  # [1]是漫画名称
    if not (download_res[0]):
        downloading_queue.remove(comic_id)
        await bot.send(ev, f"Failed to download comic {comic_id}.")
        return
    # 开始做加密
    ok, msg = await process_file(comic_id)
    if not (ok):
        downloading_queue.remove(comic_id)
        await bot.send(ev, f"加密失败！\n {msg}")
        return
    downloading_queue.remove(comic_id)
    await bot.send(ev, f"Comic {comic_id} is uploading...")
    await do_upload(bot, ev, comic_id)

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