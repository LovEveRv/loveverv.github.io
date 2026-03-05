$(function () {
    $("a").click(function () {
        var target = $(this).attr("href");
        if (!target || target[0] !== "#") {
            return;
        }
        if (target === "#") {
            $("html, body").animate({ scrollTop: "0px" }, 400);
        } else {
            var node = $(target);
            if (node.length > 0) {
                $("html, body").animate({ scrollTop: node.offset().top - 15 + "px" }, 400);
            }
        }
    });
});
