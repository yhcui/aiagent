"""渠道管理器"""
from loguru import logger
from app.models.channel import Channel
from app.services.storage_service import StorageService


class ChannelManager:
    """管理渠道注册、提示词加载"""

    def __init__(self, storage: StorageService):
        self.storage = storage
        self._channels = {}
        self.reload()

    def reload(self):
        """从数据库重新加载所有渠道"""
        self._channels = {}
        for ch in self.storage.get_all_channels():
            self._channels[ch.name] = ch
        logger.info(f"渠道管理器加载了 {len(self._channels)} 个渠道")

    def get_channel(self, name: str) -> Channel | None:
        return self._channels.get(name)

    def get_all_channels(self) -> list[Channel]:
        return list(self._channels.values())

    def get_active_channels(self) -> list[Channel]:
        return [ch for ch in self._channels.values() if ch.is_active]

    def get_system_prompt(self, channel_name: str) -> str:
        ch = self.get_channel(channel_name)
        if ch:
            return ch.system_prompt
        # 回退到内置微信公众号
        logger.warning(f"渠道 {channel_name} 未找到，使用内置微信公众号提示词")
        wechat = self.get_channel("wechat")
        return wechat.system_prompt if wechat else ""

    def add_channel(self, channel: Channel):
        self.storage.save_channel(channel)
        self._channels[channel.name] = channel
        logger.info(f"新增渠道：{channel.display_name}（{channel.name}）")

    def update_channel(self, channel: Channel):
        self.storage.save_channel(channel)
        self._channels[channel.name] = channel
        logger.info(f"更新渠道：{channel.display_name}（{channel.name}）")
