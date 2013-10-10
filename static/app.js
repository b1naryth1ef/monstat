var options = {

    title: {
        text: ''
    },

    subtitle: {
        text: ''
    },
    xAxis: {
      type: "datetime",
    },

    yAxis: { // left y axis
        title: {
            text: null
        },
        labels: {
            align: 'left',
            x: 3,
            y: 16,
            formatter: function() {
                return Highcharts.numberFormat(this.value, 0);
            }
        },
        showFirstLabel: false
    },


    legend: {
        align: 'left',
        verticalAlign: 'top',
        y: 20,
        floating: true,
        borderWidth: 0
    },

    tooltip: {
        shared: true,
        crosshairs: true
    },

    plotOptions: {
        series: {
            dataLabels: {
                      pointFormat: "{point.y:.2f}",
                        enabled: false
                    },
            animation: false,
            cursor: 'pointer',
            point: {
                events: {
                    click: function() {
                        hs.htmlExpand(null, {
                            pageOrigin: {
                                x: this.pageX,
                                y: this.pageY
                            },
                            headingText: this.series.name,
                            width: 200
                        });
                    }
                }
            },
            marker: {
                lineWidth: 1,
                enabled: false
            }
        }
    },

    series: [{
        name: 'Exceptions',
        lineWidth: 4,
        marker: {
            radius: 4
        },
        data: []
    }]
  }

function renderGraph(id, data) {
    if (!$('#'+id).length) {
        $("#add").append('<div class="row-fluid graph" id="'+id+'"></div>')
    }
    var id = $('#'+id)
    var opt = $.extend({}, options);
    var series = []
    $.each(data, function (i, v) {
        var cur = {};
        cur['name'] = v.name
        cur.data = []
        $.each(v.data, function (_i, _v) {
            cur.data.push([new Date(_v[0]).getTime(), _v[1]])
        })
        series.push(cur)
    })
    opt.series = series;
    $(id).highcharts(opt)
}
