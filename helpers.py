import discord
def fullCapitalize(string):
    string = string.lower()
    split = string.split()
    capitalizedString = ""
    for word in split:
        capitalizedString += word.capitalize() + " "
    return capitalizedString[:-1]


# deletes all messages in any number of given lists, then clears the lists
async def deleteMessages(messageList, *moreMessageLists):
    for msg in messageList:
        try:
            await msg.delete()
        except discord.errors.NotFound:
            print("message not found, this should not be happening persistently but it might be an out of "
                  "order error if it's occasional")
    messageList.clear()

    for msgList in moreMessageLists:
        print("deleting additional messages")
        await deleteMessages(msgList)


class MessagableUser():
    def __init__(self, user):
        self.user = user
        self._messagesToDeleteAfterNextMessage = []
        self._messagesToDeleteOnCommand = []

    async def send(self, content="", deletionInterval="nextMessage", *, tts=False, embed=None, file=None, files=None, delete_after=None, nonce=None, allowed_mentions=None):
        await deleteMessages(self._messagesToDeleteAfterNextMessage)
        msg = await self.user.send(content=content, tts=tts, embed=embed, file=file, files=files, delete_after=delete_after, nonce=nonce)   # allowed mentions doesnt work for some reason ?!
        if deletionInterval == "nextMessage":
            self._messagesToDeleteAfterNextMessage.append(msg)
        if deletionInterval == "command":
            self._messagesToDeleteOnCommand.append(msg)
        return msg

    async def delete(self):
        await deleteMessages(self._messagesToDeleteOnCommand)

    def __eq__(self, other):
        if isinstance(other, MessagableUser):
            return self.user == other.user
        if isinstance(other, discord.User) or isinstance(other, discord.Member):
            return self.user == other
