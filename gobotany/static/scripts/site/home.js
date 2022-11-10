require([
    "util/news"
], function (News) {
    $(document).ready(function () {
        if ($("body.home").length > 0) {   // Only show on home page for now
            var news = new News();
            news.showDialog();
        }
    });
});
