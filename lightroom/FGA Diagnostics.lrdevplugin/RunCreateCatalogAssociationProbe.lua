local LrDialogs = import("LrDialogs")
local LrFunctionContext = import("LrFunctionContext")
local LrTasks = import("LrTasks")

local CatalogAssociationProbe = require("CatalogAssociationProbe")

LrTasks.startAsyncTask(function()
    LrFunctionContext.callWithContext("createFgaCatalogAssociationProbe", function(context)
        LrDialogs.attachErrorDialogToFunctionContext(context)
        CatalogAssociationProbe.run("create_association", CatalogAssociationProbe.createAssociation)
    end)
end)
