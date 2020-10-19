CTFd.plugin.run((_CTFd) => {
    const $ = _CTFd.lib.$
    
    // https://stackoverflow.com/questions/13627308/add-st-nd-rd-and-th-ordinal-suffix-to-a-number/13627586#13627586
    function ordinalize(i) {
		var j = i % 10,
		    k = i % 100;
		if (j == 1 && k != 11) {
		    return i + "st";
		}
		if (j == 2 && k != 12) {
		    return i + "nd";
		}
		if (j == 3 && k != 13) {
		    return i + "rd";
		}
		return i + "th";
	}
    
    let bonus_points_div = $(".bonus-points");
    function update_bonus_points() {
    	let inputs = bonus_points_div.find(".bonus-points-val");
        let last_filled = -1;
    	inputs.each(function() {
    		if ($(this).find("input").val() !== '') {
    			let index = $(this).data('index');
    			if (index > last_filled)
    				last_filled = index;
    		}
    	});
    	
    	if (inputs.length >= last_filled + 2) {
	    	inputs.each(function() {
	    		if ($(this).data('index') > last_filled + 1)
	    			$(this).remove();
	    	});
	    } else {
	    	let index = inputs.length;
	    	bonus_points_div.append(`
<div class="form-group bonus-points-val" data-index="${index}">
		<label for="value">Bonus points for ${ordinalize(index + 1)} solve<br>
			<small class="form-text text-muted">
				The award for the ${ordinalize(index + 1)} team to solve the challenge
			</small>
		</label>
		<input type="number" class="form-control" name="first_blood_bonus[${index}]">
	</div>
`);
	    }
    }
    
    bonus_points_div.on("change", "input", update_bonus_points);
    $(update_bonus_points);
});
