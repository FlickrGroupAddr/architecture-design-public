local LrDialogs = import("LrDialogs")
local LrFunctionContext = import("LrFunctionContext")

local DirectUploadProbe = require("DirectUploadProbe")

LrFunctionContext.postAsyncTaskWithContext("runFgaDirectUploadProbe", function(context)
    LrDialogs.attachErrorDialogToFunctionContext(context)
    DirectUploadProbe.run(context)
end)
