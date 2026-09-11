local LrDialogs = import("LrDialogs")
local LrFunctionContext = import("LrFunctionContext")
local LrTasks = import("LrTasks")

local CatalogAssociationProbe = require("CatalogAssociationProbe")

LrTasks.startAsyncTask(function()
    LrFunctionContext.callWithContext("prepareFgaCatalogAssociationProbe", function(context)
        LrDialogs.attachErrorDialogToFunctionContext(context)
        CatalogAssociationProbe.run("prepare", CatalogAssociationProbe.prepare)
    end)
end)
