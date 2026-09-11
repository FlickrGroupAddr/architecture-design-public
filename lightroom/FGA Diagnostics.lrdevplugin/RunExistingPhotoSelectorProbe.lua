local LrDialogs = import("LrDialogs")
local LrFunctionContext = import("LrFunctionContext")
local LrTasks = import("LrTasks")

local ExistingPhotoSelectorProbe = require("ExistingPhotoSelectorProbe")

LrTasks.startAsyncTask(function()
    LrFunctionContext.callWithContext("runFgaExistingPhotoSelectorProbe", function(context)
        LrDialogs.attachErrorDialogToFunctionContext(context)
        ExistingPhotoSelectorProbe.run(context)
    end)
end)
