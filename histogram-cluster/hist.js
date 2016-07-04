// logy(x)
function getBaseLog(x, y) {
    return Math.log(x) / Math.log(y);
}

function histogram(jsonData) {
	var margin = {top: 70, right: 100, bottom: 150, left: 200},
		width = 620 - margin.left - margin.right,
		height = 520 - margin.top - margin.bottom,
	    padding = 30;
	
	var scoreScale = d3.scale.linear() 
	.domain([0, d3.max(jsonData.map(function(d) { return d.score; }))])//[0, 1]) 
	.range([height, 0]);
	
	var xScale = d3.scale
//	.linear()
//	.domain([0, 10])
//	.range([height - padding, padding]);
	.ordinal() 
	.domain(jsonData.map(function(d) { return d.name; })) 
	.rangeRoundBands([0, width], .1);
	
	//Set up the axes
	var xAxis = d3.svg.axis()
	.scale(xScale)
	.orient("bottom");
	
	var yAxis = d3.svg.axis()
	.scale(scoreScale)
	.orient("left");
	
	var hist = d3.select("svg.histogram")
	.attr("width", width + margin.left + margin.right)
	.attr("height", height + margin.top + margin.bottom);
	
	hist.select("g.xaxis")
//    .attr("class", "xaxis")
    .attr("transform", "translate("+margin.left+", " + (height+margin.top) + ")")
    .call(xAxis)
    .selectAll("text")
	.attr("y", 9)
	.attr("x", 9)
	.attr("dy", ".35em")
	.attr("transform", "rotate(45)")
	.style("text-anchor", "start");
	
	hist.select("g.yaxis")
//	.attr("class", "yaxis")
	.attr("transform", "translate("+margin.left+", "+(margin.top)+")")
	.call(yAxis);
//	.attr("transform", function(d, i) { return "translate(" + (sx(d.name)
//			+margin.left) + ", " + (margin.top+sy(d.value)) + ")"; });
//			...
//			.attr("width", sx.rangeBand());

	var bar = hist.selectAll("g.candidate");
	
	//Add tooltip function
	var tip = d3.tip()
	.attr('class', 'd3-tip')
	.offset([-10, 0])
	.html(function (d) {
//	alert(d.name+', '+d.score);
	return d.name+', '+d.score;
	});
	hist.call(tip);

//	alert('Done 1');
	
	var barUpdate = bar.data(jsonData);
	// Add the new g elements by a translation of 20x
	var barEnter = barUpdate.enter().append("g")
	.attr("class", "candidate");
	// Fill each g with a rectangle
	barEnter.append("rect")
	.attr("width", xScale.rangeBand())
	.on('mouseover', tip.show)
	.on('mouseout', tip.hide);
//	// Add a text to each g
//	barEnter.append("text") 
//	.attr("y", 300);
	
//	alert('Done 2');
	
	// Remove old elements that havent been replaced
	var barExit = barUpdate.exit().remove();
	// Update values
	barUpdate.select("rect")
	.attr("height", function(d) {
//		alert(scoreScale(d.score)+", "+ d.score);
		return height - scoreScale(d.score); });//scoreScale(d.score); });
	
//	alert('Done 3');
	
	// Set g position
	barUpdate.attr("transform", function(d, i) { 
		return "translate(" 
//		+ (xScale(d.name) +margin.left) + ", 0)";});//  + (margin.top+yAxis(d.score)) + ")"; });
		+ (xScale(d.name)+margin.left)+ ", "+ (margin.top  +scoreScale(d.score)) +")"; });//(height + margin.top - scoreScale(d.score)) + ")"; });
//	// Add a text to each g
//	barUpdate.select("text") 
//	.attr("x", function(d) { return 1;})//scoreScale(d.score); }) 
//	.text(function(d) { return d.score; });
	
//	alert('Done');
	
}


function initPat(dataset) {
	var patTerms = Object.keys(dataset);
	var select = d3.select('div#patList')
	  .append('select')
	  	.attr('id','patList');

	var options = select
	  .selectAll('option')
		.data(patTerms).enter()
		.append('option')
		.attr('value', function (d) { return d; })
			.text(function (d) { return d; });
	
	function onchange() {
		selectValue = d3.select('select#patList').property('value');
//		alert(selectValue);
		histogram(eval('dataset[\"'+selectValue+'\"]'));
//		d3.select('body')
//			.append('p')
//			.text(selectValue + ' is the last selected option.');
	};
	
	select.on('change', onchange);
	
}


// Read in .csv data and make graph
d3.json("align.json",function(error, json) {
	  if (error) return console.warn(error);
	  dataset = json;
	  var patTerms = Object.keys(dataset);
	  initPat(dataset);
	  histogram(eval('dataset[\"'+patTerms[0]+'\"]'));
	  }
); 
