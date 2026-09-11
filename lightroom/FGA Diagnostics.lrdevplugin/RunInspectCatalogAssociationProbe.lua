local LrDialogs = import("LrDialogs")
local LrFunctionContext = import("LrFunctionContext")
local LrTasks = import("LrTasks")

local CatalogAssociationProbe = require("CatalogAssociationProbe")

LrTasks.startAsyncTask(function()
    LrFunctionContext.callWithContext("inspectFgaCatalogAssociationProbe", function(context)
        LrDialogs.attachErrorDialogToFunctionContext(context)
        CatalogAssociationProbe.run("inspect", CatalogAssociationProbe.inspect)
    end)
end)
