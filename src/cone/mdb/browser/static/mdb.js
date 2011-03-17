/* 
 * mdb JS
 * 
 * Requires:
 *     bdajax
 *     jquery ui autocomplete
 */

if (typeof(window['yafowil']) == "undefined") yafowil = {};

(function($) {

    $(document).ready(function() {
        
        // initial binding
        mdb.transitionmenubinder();
        
        // add binder to bdajax binding callbacks
        $.extend(bdajax.binders, {
            transitionmenubinder: mdb.transitionmenubinder
        });
    });
    
    mdb = {
    
        transitionmenubinder: function(context) {
            $('.transitions_dropdown', context).dropdownmenu({
                menu: '.dropdown_items',
                trigger: '.state a'
            });
        }
    }

})(jQuery);