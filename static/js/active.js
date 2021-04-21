(function($){'use strict';var browserWindow=$(window);browserWindow.on('load',function(){$('#preloader').fadeOut('slow',function(){$(this).remove();});});$.simpleTicker($("#breakingNewsTicker"),{speed:1000,delay:3000,easing:'swing',effectType:'roll'});$.simpleTicker($("#internationalTicker"),{speed:1000,delay:4000,easing:'swing',effectType:'roll'});if($.fn.classyNav){$('#newspaperNav').classyNav();}
if($.fn.magnificPopup){$('.videoPlayer').magnificPopup({type:'iframe'});}
if($.fn.scrollUp){browserWindow.scrollUp({scrollSpeed:1500,scrollText:'<i class="fa fa-angle-up"></i>'});}
if($.fn.counterUp){$('.counter').counterUp({delay:10,time:2000});}
if($.fn.sticky){$("#stickyMenu").sticky({topSpacing:0});}
if(browserWindow.width()>767){new WOW().init();}
$('a[href="#"]').click(function($){$.preventDefault()});})(jQuery);