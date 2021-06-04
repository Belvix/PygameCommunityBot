"""
This file is a part of the source code for the PygameCommunityBot.
This project has been licensed under the MIT license.
Copyright (c) 2020-present PygameCommunityDiscord

This file defines the command handler class for the sudo commands of the bot
"""


from __future__ import annotations

import asyncio
import datetime
import io
import os
from typing import Optional, Union

import discord
import psutil

from pgbot import common
from pgbot.utils import embed_utils, utils
from pgbot.commands.base import BaseCommand, BotException, String, add_group

process = psutil.Process(os.getpid())


class SudoCommand(BaseCommand):
    """
    Base class for all sudo commands
    """

    @add_group("sudo")
    async def cmd_sudo(
        self,
        *datas: Union[discord.Message, String],
        destination: Optional[discord.TextChannel] = None,
        from_attachment: bool = True,
    ):
        """
        ->type More admin commands
        ->signature pg!sudo <msg>
        ->description Send a message through the bot
        ->extended description
        Send a sequence of messages contain text from the given
        data using the specified arguments.

        __Args__:
            `*datas: (Message|String)`
            > A sequence of discord messages whose text
            > or text attachment should be used as input,
            > or strings.

            `destination (TextChannel) = `
            > A destination channel to send the output to.

            `from_attachment (bool) = True`
            > Whether the attachment of an input message should be
            > used to create a message.

        __Returns__:
            > One or more generated messages based on the given input.

        __Raises__:
            > `BotException`: One or more given arguments are invalid.
            > `HTTPException`: An invalid operation was blocked by Discord.

        ->example command
        pg!sudo "lol" "that" "was" "funny /s" destination=#general
        pg!sudo 987654321987654321 "Additionally, ..." 123456739242423 from_attachment=True
        -----
        Implement pg!sudo, for admins to send messages via the bot
        """

        if not isinstance(destination, discord.TextChannel):
            destination = self.channel

        if not utils.check_channel_permissions(
            self.author, destination, permissions=("view_channel", "send_messages")
        ):
            raise BotException(
                f"Not enough permissions",
                "You do not have enough permissions to run this command with the specified arguments.",
            )

        for i, data in enumerate(datas):
            if isinstance(data, discord.Message):
                if not utils.check_channel_permissions(
                    self.author,
                    data.channel,
                    permissions=("view_channel",),
                ):
                    raise BotException(
                        f"Not enough permissions",
                        "You do not have enough permissions to run this command with the specified arguments.",
                    )

            if not i % 50:
                await asyncio.sleep(0)

        output_strings = []
        load_embed = embed_utils.create(
            title=f"Your command is being processed:",
            fields=(
                ("\u2800", "`...`", False),
                ("\u2800", "`...`", False),
            ),
        )
        data_count = len(datas)
        for i, data in enumerate(datas):
            if data_count > 2 and not i % 3:
                await embed_utils.edit_field_from_dict(
                    self.response_msg,
                    load_embed,
                    dict(
                        name="Processing Inputs",
                        value=f"`{i}/{data_count}` inputs processed\n"
                        f"{(i/data_count)*100:.01f}% | "
                        + utils.progress_bar(i / data_count, divisions=30),
                    ),
                    0,
                )
            attachment_msg = None

            if isinstance(data, String):
                if not data.string:
                    attachment_msg = self.invoke_msg
                else:
                    msg_text = data.string
                    output_strings.append(msg_text)

            elif isinstance(data, discord.Message):
                if not utils.check_channel_permissions(
                    self.author,
                    data.channel,
                    permissions=("view_channel",),
                ):
                    raise BotException(
                        f"Not enough permissions",
                        "You do not have enough permissions to run this command with the specified arguments.",
                    )
                if from_attachment:
                    attachment_msg = data
                else:
                    src_msg_txt = data.content
                    if src_msg_txt:
                        output_strings.append(src_msg_txt)
                    else:
                        raise BotException(
                            f"Input {i}: No message text found!",
                            "The message given as input does not have any text content.",
                        )

            if attachment_msg:
                if not attachment_msg.attachments:
                    raise BotException(
                        f"Input {i}: No valid attachment found in message.",
                        "It must be a `.txt` file containing text data."
                        " If you want to retrieve the content of the"
                        " given message(s) instead, set the"
                        "` from_attachment=` argument to `False`",
                    )

                for attachment in attachment_msg.attachments:
                    if (
                        attachment.content_type is not None
                        and attachment.content_type.startswith(("text"))
                    ):
                        attachment_obj = attachment
                        break
                else:
                    raise BotException(
                        f"Input {i}: No valid attachment found in message.",
                        "It must be a `.txt` file containing text data.",
                    )

                msg_text = await attachment_obj.read()
                msg_text = msg_text.decode()

                if 0 < len(msg_text) <= 2000:
                    output_strings.append(msg_text)
                else:
                    raise BotException(
                        f"Input {i}: Too little/many characters!",
                        "a Discord message must contain at least one character and cannot contain more than 2000.",
                    )

            await asyncio.sleep(0)

        if not datas:
            data_count = 1
            attachment_msg = self.invoke_msg
            if not attachment_msg.attachments:
                raise BotException(
                    "No valid attachment found in message.",
                    "It must be a `.txt` file containing text data.",
                )

            for attachment in attachment_msg.attachments:
                if (
                    attachment.content_type is not None
                    and attachment.content_type.startswith(("text"))
                ):
                    attachment_obj = attachment
                    break
            else:
                raise BotException(
                    "No valid attachment found in message.",
                    "It must be a `.txt` file containing text data.",
                )

            msg_text = await attachment_obj.read()
            msg_text = msg_text.decode()

            if 0 < len(msg_text) <= 2000:
                output_strings.append(msg_text)
            else:
                raise BotException(
                    f"Too little/many characters!",
                    "a Discord message must contain at least one character and cannot contain more than 2000.",
                )

        if data_count > 2:
            await embed_utils.edit_field_from_dict(
                self.response_msg,
                load_embed,
                dict(
                    name="Processing Completed",
                    value=f"`{data_count}/{data_count}` inputs processed\n"
                    f"100% | " + utils.progress_bar(1.0, divisions=30),
                ),
                0,
            )

        output_count = len(output_strings)
        for j, msg_txt in enumerate(output_strings):
            if output_count > 2 and not j % 3:
                await embed_utils.edit_field_from_dict(
                    self.response_msg,
                    load_embed,
                    dict(
                        name="Creating Messages",
                        value=f"`{j}/{output_count}` messages created\n"
                        f"{(j/output_count)*100:.01f}% | "
                        + utils.progress_bar(j / output_count, divisions=30),
                    ),
                    1,
                )
            await destination.send(content=msg_txt)

        if data_count > 2:
            await embed_utils.edit_field_from_dict(
                self.response_msg,
                load_embed,
                dict(
                    name="Creation Completed",
                    value=f"`{output_count}/{output_count}` messages created\n"
                    f"100% | " + utils.progress_bar(1.0, divisions=30),
                ),
                1,
            )

        await self.response_msg.delete(delay=10.0 if data_count > 1 else 0.0)
        await self.invoke_msg.delete()

    @add_group("sudo", "edit")
    async def cmd_sudo_edit(
        self,
        edit_msg: discord.Message,
        data: Union[discord.Message, String],
        from_attachment: bool = True,
    ):
        """
        ->type More admin commands
        ->signature pg!sudo_edit <edit_msg> <data> [from_attachment=True]
        ->description Edit a message that the bot sent.
        ->extended description
        If `from_attachment=` is set to `True`, the attachment of the given message
        will be used for editing the target message.
        -----
        Implement pg!sudo_edit, for admins to edit messages via the bot
        """

        if not utils.check_channel_permissions(
            self.author,
            edit_msg.channel,
            permissions=("view_channel", "send_messages"),
        ):
            raise BotException(
                f"Not enough permissions",
                "You do not have enough permissions to run this command with the specified arguments.",
            )

        elif isinstance(data, discord.Message) and not utils.check_channel_permissions(
            self.author,
            data.channel,
            permissions=("view_channel",),
        ):
            raise BotException(
                f"Not enough permissions",
                "You do not have enough permissions to run this command with the specified arguments.",
            )

        attachment_msg: Optional[discord.Message] = None
        msg_text = ""

        if isinstance(data, String):
            if not data.string:
                attachment_msg = self.invoke_msg
            else:
                msg_text = data.string

        elif isinstance(data, discord.Message):
            if from_attachment:
                attachment_msg = data
            else:
                src_msg_txt = data.content
                if src_msg_txt:
                    msg_text = src_msg_txt
                else:
                    raise BotException(
                        "No message text found!",
                        "The message given as input does not have any text content.",
                    )

        if attachment_msg:
            if not attachment_msg.attachments:
                raise BotException(
                    "No valid attachment found in message.",
                    "It must be a `.txt` file containing text data.",
                )

            for attachment in attachment_msg.attachments:
                if (
                    attachment.content_type is not None
                    and attachment.content_type.startswith(("text"))
                ):
                    attachment_obj = attachment
                    break
            else:
                raise BotException(
                    "No valid attachment found in message.",
                    "It must be a `.txt` file containing text data.",
                )

            msg_text = await attachment_obj.read()
            msg_text = msg_text.decode()

            if not 0 < len(msg_text) <= 2000:
                raise BotException(
                    f"Too little/many characters!",
                    "a Discord message must contain at least one character and cannot contain more than 2000.",
                )
        try:
            await edit_msg.edit(content=msg_text)
        except discord.HTTPException as e:
            raise BotException(
                "An exception occured while handling the command!", e.args[0]
            )
        await self.invoke_msg.delete()
        await self.response_msg.delete()
        return

    @add_group("sudo", "get")
    async def cmd_sudo_get(
        self,
        *msgs: discord.Message,
        destination: Optional[discord.TextChannel] = None,
        as_attachment: bool = False,
        info: bool = False,
        attachments: bool = True,
        embeds: bool = True,
    ):
        """
        ->type More admin commands
        ->signature pg!sudo_get <*messages> [destination=] [as_attachment] [info] [attachments] [embeds]
        ->description Get the text of messages through the bot
        ->extended description
        Get the contents, attachments and embeds of messages from the given arguments and send it in multiple message attachments
        to the channel where this command was invoked. If `as_attachment=` is set to `True`, the message data will
        be returned in `.txt` files.
        -----
        Implement pg!sudo_get, to return the the contents of a message as an embed or in a text file.
        """
        if not isinstance(destination, discord.TextChannel):
            destination = self.channel

        if not utils.check_channel_permissions(
            self.author, destination, permissions=("view_channel", "send_messages")
        ):
            raise BotException(
                f"Not enough permissions",
                "You do not have enough permissions to run this command with the specified arguments.",
            )

        checked_channels = set()
        for i, msg in enumerate(msgs):
            if not msg.channel in checked_channels:
                if not utils.check_channel_permissions(
                    self.author, msg.channel, permissions=("view_channel",)
                ):
                    raise BotException(
                        f"Not enough permissions",
                        "You do not have enough permissions to run this command with the specified arguments.",
                    )
                else:
                    checked_channels.add(msg.channel)

            if not i % 50:
                await asyncio.sleep(0)

        load_embed = embed_utils.create(
            title=f"Your command is being processed:",
            fields=(("\u2800", "`...`", False),),
        )

        msg_count = len(msgs)
        for i, msg in enumerate(msgs):
            if msg_count > 2 and not i % 3:
                await embed_utils.edit_field_from_dict(
                    self.response_msg,
                    load_embed,
                    dict(
                        name="Processing Messages",
                        value=f"`{i}/{msg_count}` messages processed\n"
                        f"{(i/msg_count)*100:.01f}% | "
                        + utils.progress_bar(i / msg_count, divisions=30),
                    ),
                    0,
                )
            await destination.trigger_typing()
            attached_files = None
            if attachments:
                with io.StringIO("This file was too large to be duplicated.") as fobj:
                    file_size_limit = (
                        msg.guild.filesize_limit
                        if msg.guild
                        else common.GUILD_MAX_FILE_SIZE
                    )
                    attached_files = [
                        (
                            await a.to_file(spoiler=a.is_spoiler())
                            if a.size <= file_size_limit
                            else discord.File(fobj, f"filetoolarge - {a.filename}.txt")
                        )
                        for a in msg.attachments
                    ]

            if info:
                info_embed = embed_utils.get_msg_info_embed(msg)
                info_embed.set_author(name="Message data & info")
                info_embed.title = ""
                info_embed.description = f"```\n{msg.content}```\n\u2800"

                content_file = None
                if as_attachment and msg.content:
                    with io.StringIO(msg.content) as fobj:
                        content_file = discord.File(fobj, "messagedata.txt")

                await destination.send(embed=info_embed, file=content_file)

            elif as_attachment:
                with io.StringIO(msg.content) as fobj:
                    await destination.send(
                        file=discord.File(fobj, "messagedata.txt"),
                        embed=embed_utils.create(
                            author_name="Message data",
                            description=f"**[View Original Message]({msg.jump_url})**",
                            color=0xFFFFAA,
                        ),
                    )

            else:
                await embed_utils.send_2(
                    self.channel,
                    author_name="Message data",
                    description="```\n{0}```".format(
                        msg.content.replace("```", "\\`\\`\\`")
                    ),
                    fields=(
                        (
                            "\u2800",
                            f"**[View Original Message]({msg.jump_url})**",
                            False,
                        ),
                    ),
                )

            if attached_files:
                for i in range(len(attached_files)):
                    await self.channel.send(
                        content=f"**Message attachment** ({i+1}):",
                        file=attached_files[i],
                    )

            if embeds and msg.embeds:
                embed_data_fobjs = []
                for embed in msg.embeds:
                    embed_data_fobj = io.StringIO()
                    embed_utils.export_embed_data(
                        embed.to_dict(),
                        fp=embed_data_fobj,
                        indent=4,
                        as_json=True,
                    )
                    embed_data_fobj.seek(0)
                    embed_data_fobjs.append(embed_data_fobj)

                for i in range(len(embed_data_fobjs)):
                    await self.channel.send(
                        content=f"**Message embed** ({i+1}):",
                        file=discord.File(
                            embed_data_fobjs[i], filename="embeddata.json"
                        ),
                    )

                for embed_data_fobj in embed_data_fobjs:
                    embed_data_fobj.close()

            await asyncio.sleep(0)

        if msg_count > 2:
            await embed_utils.edit_field_from_dict(
                self.response_msg,
                load_embed,
                dict(
                    name="Processing Completed",
                    value=f"`{msg_count}/{msg_count}` messages processed\n"
                    f"100% | " + utils.progress_bar(1.0, divisions=30),
                ),
                0,
            )

        await self.response_msg.delete(delay=10 if msg_count > 1 else 0)

    @add_group("sudo", "fetch")
    async def cmd_sudo_fetch(
        self,
        origin: discord.TextChannel,
        quantity: int,
        urls: bool = False,
        pinned: bool = False,
        pin_range: Optional[range] = None,
        before: Optional[Union[discord.Message, datetime.datetime]] = None,
        after: Optional[Union[discord.Message, datetime.datetime]] = None,
        around: Optional[Union[discord.Message, datetime.datetime]] = None,
        oldest_first: bool = True,
        prefix: String = String(""),
        sep: String = String(" "),
        suffix: String = String(""),
    ):
        """
        ->type More admin commands
        ->signature pg!sudo_fetch <origin channel> <quantity> [urls=False] [pinned=False] [before=None]
        [after=None] [around=None] [oldest_first=True] [prefix=""] [sep=" "] [suffix=""]
        ->description Fetch messages IDs or URLs
        -----
        Implement pg!sudo_fetch, for admins to fetch several message IDs and links at once
        """

        if not utils.check_channel_permissions(
            self.author,
            origin,
            permissions=("view_channel",),
        ):
            raise BotException(
                f"Not enough permissions",
                "You do not have enough permissions to run this command on the specified channel.",
            )

        prefix = prefix.string
        sep = sep.string
        suffix = suffix.string

        destination = self.channel

        if pinned:
            messages = await origin.pins()
            if not messages:
                raise BotException(
                    "No pinned messages found",
                    "No pinned messages were found in the specified channel.",
                )

            if not oldest_first:
                messages.reverse()

            if quantity > 0:
                messages = messages[: quantity + 1]

            elif quantity == 0:
                if pin_range:
                    messages = messages[
                        pin_range.start : pin_range.stop : pin_range.step
                    ]

            elif quantity < 0:
                raise BotException(
                    "Invalid `quantity` argument",
                    "Quantity has to be a positive integer (`=> 0`).",
                )

        else:
            if isinstance(before, discord.Message) and before.channel.id != origin.id:
                raise BotException(
                    "Invalid `before` argument",
                    "`before` has to be an ID to a message from the origin channel",
                )

            if isinstance(after, discord.Message) and after.channel.id != origin.id:
                raise BotException(
                    "Invalid `after` argument",
                    "`after` has to be an ID to a message from the origin channel",
                )

            if isinstance(around, discord.Message) and around.channel.id != origin.id:
                raise BotException(
                    "Invalid `around` argument",
                    "`around` has to be an ID to a message from the origin channel",
                )

            if quantity <= 0:
                if quantity == 0 and not after:
                    raise BotException(
                        "Invalid `quantity` argument",
                        "`quantity` must be above 0 when `after=` is not specified.",
                    )
                elif quantity != 0:
                    raise BotException(
                        "Invalid `quantity` argument",
                        "Quantity has to be a positive integer (or `0` when `after=` is specified).",
                    )

            await destination.trigger_typing()
            messages = await origin.history(
                limit=quantity if quantity != 0 else None,
                before=before,
                after=after,
                around=around,
            ).flatten()

            if not messages:
                raise BotException(
                    "Invalid time range",
                    "No messages were found for the specified input values.",
                )

            if not after and oldest_first:
                messages.reverse()

        if urls:
            output_filename = "message_urls.txt"
            output_str = prefix + sep.join(msg.jump_url for msg in messages) + suffix
        else:
            output_filename = "message_ids.txt"
            output_str = prefix + sep.join(str(msg.id) for msg in messages) + suffix

        with io.StringIO(output_str) as fobj:
            try:
                await destination.send(
                    file=discord.File(fobj, filename=output_filename)
                )
            except discord.HTTPException as e:
                raise BotException("Something went wrong", e.args[0])

        await self.response_msg.delete()

    @add_group("sudo", "clone")
    async def cmd_sudo_clone(
        self,
        *msgs: discord.Message,
        destination: Optional[discord.TextChannel] = None,
        embeds: bool = True,
        attachments: bool = True,
        as_spoiler: bool = False,
        info: bool = False,
        author_info: bool = False,
    ):
        """
        ->type More admin commands
        ->signature pg!sudo_clone <*messages> [destination=] [embeds=True] [attachments=True]
        [as_spoiler=False] [info=False] [author_info=False]
        ->description Clone a message through the bot
        ->extended description
        Get a message from the given arguments and send it as another message to the channel where this command was invoked.
        -----
        Implement pg!sudo_clone, to get the content of a message and send it.
        """

        if not isinstance(destination, discord.TextChannel):
            destination = self.channel

        if not utils.check_channel_permissions(
            self.author, destination, permissions=("view_channel", "send_messages")
        ):
            raise BotException(
                f"Not enough permissions",
                "You do not have enough permissions to run this command with the specified arguments.",
            )

        checked_channels = set()
        for i, msg in enumerate(msgs):
            if not msg.channel in checked_channels:
                if not utils.check_channel_permissions(
                    self.author, msg.channel, permissions=("view_channel",)
                ):
                    raise BotException(
                        f"Not enough permissions",
                        "You do not have enough permissions to run this command with the specified arguments.",
                    )
                else:
                    checked_channels.add(msg.channel)

            if not i % 50:
                await asyncio.sleep(0)

        load_embed = embed_utils.create(
            title=f"Your command is being processed:",
            fields=(("\u2800", "`...`", False),),
        )

        msg_count = len(msgs)
        no_mentions = discord.AllowedMentions.none()
        for i, msg in enumerate(msgs):
            if msg_count > 2 and not i % 3:
                await embed_utils.edit_field_from_dict(
                    self.response_msg,
                    load_embed,
                    dict(
                        name="Processing Messages",
                        value=f"`{i}/{msg_count}` messages processed\n"
                        f"{(i/msg_count)*100:.01f}% | "
                        + utils.progress_bar(i / msg_count, divisions=30),
                    ),
                    0,
                )

            await destination.trigger_typing()
            cloned_msg = None
            attached_files = []
            if msg.attachments and attachments:
                with io.StringIO("This file was too large to be cloned.") as fobj:
                    file_size_limit = (
                        msg.guild.filesize_limit
                        if msg.guild
                        else common.GUILD_MAX_FILE_SIZE
                    )
                    attached_files = [
                        (
                            await a.to_file(spoiler=a.is_spoiler() or as_spoiler)
                            if a.size <= file_size_limit
                            else discord.File(fobj, f"filetoolarge - {a.filename}.txt")
                        )
                        for a in msg.attachments
                    ]

            if msg.content or msg.embeds or attached_files:
                cloned_msg = await destination.send(
                    content=msg.content,
                    embed=msg.embeds[0] if msg.embeds and embeds else None,
                    file=attached_files[0] if attached_files else None,
                    allowed_mentions=no_mentions,
                )
            else:
                raise BotException(f"Cannot clone an empty message!", "")

            for i in range(1, len(attached_files)):
                await self.channel.send(
                    file=attached_files[i],
                )

            for i in range(1, len(msg.embeds)):
                await self.channel.send(
                    embed=msg.embeds[i],
                )

            if info:
                await self.channel.send(
                    embed=embed_utils.get_msg_info_embed(msg, author=author_info),
                    reference=cloned_msg,
                )
            elif author_info:
                await self.channel.send(
                    embed=embed_utils.get_member_info_embed(msg.author),
                    reference=cloned_msg,
                )

            await asyncio.sleep(0)

        if msg_count > 2:
            await embed_utils.edit_field_from_dict(
                self.response_msg,
                load_embed,
                dict(
                    name="Processing Completed",
                    value=f"`{msg_count}/{msg_count}` messages processed\n"
                    f"100% | " + utils.progress_bar(1.0, divisions=30),
                ),
                0,
            )

        await self.response_msg.delete(delay=8 if msg_count > 0 else 0)

    async def cmd_info(
        self,
        *objs: Union[discord.Message, discord.Member, discord.User],
        author: bool = True,
    ):
        """
        ->type More admin commands
        ->signature pg!info <message or member> [author_bool]
        ->description Get information about a message/member

        -----
        Implement pg!info, to get information about a message/member
        """

        checked_channels = set()
        for i, obj in enumerate(objs):
            if isinstance(obj, discord.Message):
                if not utils.check_channel_permissions(
                    self.author,
                    obj.channel,
                    permissions=("view_channel",),
                ):
                    raise BotException(
                        f"Not enough permissions",
                        "You do not have enough permissions to run this command on the specified channel.",
                    )
                else:
                    checked_channels.add(obj.channel)

            if not i % 50:
                await asyncio.sleep(0)

        if not objs:
            obj = self.author
            embed = embed_utils.get_member_info_embed(obj)
            await self.channel.send(embed=embed)

        load_embed = embed_utils.create(
            title=f"Your command is being processed:",
            fields=(("\u2800", "`...`", False),),
        )
        obj_count = len(objs)
        for i, obj in enumerate(objs):
            if obj_count > 2 and not i % 3:
                await embed_utils.edit_field_from_dict(
                    self.response_msg,
                    load_embed,
                    dict(
                        name="Processing Inputs",
                        value=f"`{i}/{obj_count}` inputs processed\n"
                        f"{(i/obj_count)*100:.01f}% | "
                        + utils.progress_bar(i / obj_count, divisions=30),
                    ),
                    0,
                )
            await self.channel.trigger_typing()
            embed = None
            if isinstance(obj, discord.Message):
                embed = embed_utils.get_msg_info_embed(obj, author=author)

            elif isinstance(obj, (discord.Member, discord.User)):
                embed = embed_utils.get_member_info_embed(obj)

            if embed is not None:
                await self.channel.send(embed=embed)

            await asyncio.sleep(0)

        if obj_count > 2:
            await embed_utils.edit_field_from_dict(
                self.response_msg,
                load_embed,
                dict(
                    name="Processing Complete",
                    value=f"`{obj_count}/{obj_count}` inputs processed\n"
                    f"100% | " + utils.progress_bar(1.0, divisions=30),
                ),
                0,
            )

        await self.response_msg.delete(delay=10.0 if obj_count > 1 else 0.0)