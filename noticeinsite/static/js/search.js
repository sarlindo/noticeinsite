
//$(function(){
//    $("#searchcompany").click(function(){
//        alert($("#searchinput").val());
//        $("window").scrollTop($("*:contains('" + $("#searchinput").val() + "'):eq(1)").offset().top);
//    });
//});

$(document).ready(function () {
    $('#searchcompany').on("click", function () {
        if (!searchAndHighlight($('#searchinput').val())) {
            alert("No results found");
        }
    });
});
function searchAndHighlightOLD(searchTerm, selector) {
    if (searchTerm) {
        var selector = selector || "#product-list-container";
        var searchTermRegEx = new RegExp(searchTerm, "ig");
        var matches = $(selector).text().match(searchTermRegEx);
        if (matches) {
            $('.highlighted').removeClass('highlighted'); //Remove old search highlights
            var index;
            for (index = 0; index < matches.length; ++index) {
                var wordreg = new RegExp(matches[index]);
                $(selector).html($(selector).html()
                    .replace(wordreg, "<span class='highlighted'>" + matches[index] + "</span>"));
            }

            if ($('.highlighted:first').length) { //if match found, scroll to where the first one appears
                $(document).scrollTop($('.highlighted:first').eq(0).offset().top - 75);

            }
            return true;
        }
    }
    return false;
 }


 function searchAndHighlight(searchTerm) {
     if (searchTerm) {
         var searchTermRegEx, matches;
         var  selector= "#product-list-container";
         $(selector+' span.match').each(function(){
         $(this).replaceWith($(this).html());
       });
         try {
             searchTermRegEx = new RegExp('('+searchTerm+')', "ig");
         } catch (e) {
             return false;
         }
         $('.highlighted').removeClass('highlighted');
         matches = $(selector).text().match(searchTermRegEx);
         if (matches !==null && matches.length > 0) {
             //var txt = $(selector).text().replace(searchTermRegEx,
             //'<span class="match">$1</span>');
             //$(selector).html(txt);
             $(selector).html($(selector).html().replace(searchTermRegEx, '<span class="match">$1</span>'));
             searchIndex = 0;
             $('.match:first').addClass('highlighted');
             $(document).scrollTop($('.match').eq(searchIndex).offset().top - 75);

           return true;
         }
       return false;
     }
   return false;
 }
