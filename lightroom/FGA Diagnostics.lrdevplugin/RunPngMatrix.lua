local LrDialogs = import("LrDialogs")
local LrFunctionContext = import("LrFunctionContext")
local LrTasks = import("LrTasks")

local PngMatrix = require("PngMatrix")

LrTasks.startAsyncTask(function()
    LrFunctionContext.callWithContext("runFgaPngMatrix", function(context)
        LrDialogs.attachErrorDialogToFunctionContext(context)
        PngMatrix.run(context)
    end)
end)
