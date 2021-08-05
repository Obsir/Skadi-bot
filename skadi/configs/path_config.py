import os


def init_plugin_res_path(bot_config):
    root_path = bot_config.bot_res_path
    pixiv_path = os.path.join(root_path, 'pixiv')
    if not os.path.exists(pixiv_path):
        os.makedirs(pixiv_path)
    stick_path = os.path.join(root_path, 'stick')
    if not os.path.exists(stick_path):
        os.makedirs(stick_path)
    nhentai_path = os.path.join(root_path, 'nhentai')
    if not os.path.exists(nhentai_path):
        os.makedirs(nhentai_path)
    text2img_path = os.path.join(root_path, 'text2img')
    if not os.path.exists(text2img_path):
        os.makedirs(text2img_path)
    bot_config.pixiv_path = pixiv_path
    bot_config.stick_path = stick_path
    bot_config.nhentai_path = nhentai_path
    bot_config.text2img_path = text2img_path
