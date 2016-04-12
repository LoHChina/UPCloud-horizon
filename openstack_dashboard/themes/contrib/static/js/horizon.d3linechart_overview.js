// TODO(lsmola) write a proper doc for each attribute and method
horizon.d3_line_chart_overview = {
  LineChart: function(chart_class, html_element){
    var self = this;
    var jquery_element = $(html_element);

    self.chart_class = chart_class;
    self.html_element = html_element;

    self.url = jquery_element.data("url");
    self.url_parameters = jquery_element.data("url_parameters");

    self.data = []
    self.color = d3.scale.category20();

    self.load_settings = function(settings) {
       // TODO (lsmola) make settings work
       /* Settings will be obtained either from Json from server,
          or from init of the charts, server will have priority */
       self.settings = {};
       self.settings.renderer = 'area';
       self.settings.auto_size = true;
    }
    self.get_size = function(){
      /* The height will be determined by css or window size,
         I have to hide everything inside that could mess with
         the size, so it is fully determined by outer CSS. */
      $(self.html_element).css("height", "");
      $(self.html_element).css("width", "");
      var svg = $(self.html_element).find("svg");
      svg.hide();

      // Width an height of the chart will be taken from chart wrapper,
      // that can be styled by css.
      self.width = jquery_element.width();

      // Set either the minimal height defined by CSS.
      self.height = jquery_element.height();

      /* Setting new sizes. It is important when resizing a window.*/
      $(self.html_element).css("height", self.height);
      $(self.html_element).css("width", self.width);
      svg.show();
      svg.css("height", self.height);
      svg.css("width", self.width);
    }
    // Load initial settings.
    self.load_settings({});
    // Get correct size of chart and the wrapper.
    self.get_size();

    self.refresh = function (data){
      var self = this;
      jquery_element.html("");
      self.series = data.series;
      self.load_settings(data.settings);
      if (self.series <= 0) {
        $(self.html_element).html("No data available.");
      } else {
        var all_series_data = self.series[0].data;
        var last_series_data = all_series_data[all_series_data.length-1];
        self.render();
        var unit = self.series[0].unit;
        $('.' + self.series[0].class).html(self.format_num(last_series_data.y) + " " + unit)
      }
    };

    self.convert_to_local_time = function(date){
        var d = new Date(date + "+00:00");
        utc = d.getTime();
        return utc
    }

    self.format_num = function(y) {
        var abs_y = Math.abs(y);
        if (abs_y >= 1000000000000)   { return (y / 1000000000000).toFixed(2) + "T" }
        else if (abs_y >= 1000000000) { return (y / 1000000000).toFixed(2) + "G" }
        else if (abs_y >= 1000000)    { return (y / 1000000).toFixed(2) + "M" }
        else if (abs_y >= 1000)       { return (y / 1000).toFixed(2) + "K" }
        else if (abs_y < 1000 && y >= 0)  { return y.toFixed(2) }
        else if (abs_y < 1 && y > 0)  { return y.toFixed(2) }
        else if (abs_y === 0)         { return '' }
        else                      { return y }
    };

    self.render = function(){
      var self = this;

      $.map(self.series, function (serie) {
        $.map(serie.data, function (statistic) {
          statistic.x = d3.time.format.utc('%Y-%m-%dT%H:%M:%SZ').parse(statistic.x);
          statistic.x = statistic.x.getTime() / 1000;
        });
      });
     
      // instantiate our graph!
      var graph = new Rickshaw.Graph({
        element: self.html_element,
        width: self.width,
        height: self.height,
        renderer: self.settings.renderer,
        series: self.series,
        interpolation: 'linear',
      });

      var hoverDetail = new Rickshaw.Graph.HoverDetail({
        graph: graph,
        formatter: function(series, x, y) {
          var content = self.format_num(y) + " " + series.unit
          return content;
        }
      });

      graph.render();

      var axes_x = new Rickshaw.Graph.Axis.Time({
        graph: graph,
        timeFixture: new Rickshaw.Fixtures.Time.Local(),
      });
      axes_x.render();

      var axes_y = new Rickshaw.Graph.Axis.Y({
        graph: graph,
        tickFormat: Rickshaw.Fixtures.Number.formatKMBT,
        ticks: 2
      });
      axes_y.render();

    };
  },
  init: function(selector, settings) {
    var self = this;
    self.send_ajax(selector);
  },
  send_ajax: function(selector) {
    var self = this;
    var jquery_element = $(selector)
    self.final_url = jquery_element.data("url");
    if (jquery_element.data('form-selector')){
      $(jquery_element.data('form-selector')).each(function(){
        if (self.final_url.indexOf('?') > -1){
          self.final_url += '&' + $(this).serialize();
        } else {
          self.final_url += '?' + $(this).serialize();
        }
      });
    }

    // Retrieve the series 
    if (jquery_element.length) {
      jquery_element.empty();
      jquery_element.spin(horizon.conf.spinner_options.inline);
      $.ajax({
        url: self.final_url,
        success: function (data, textStatus, jqXHR) {
          if ($.isEmptyObject(data)) {
            jquery_element.html(gettext("No data available."));
          } else {
            $(selector).each(function() {
              var data_type = $(this).data('type');
              var data_series = data[data_type]
              if (typeof(data_series) != "undefined") {
                self.refresh(this, data_series);
              } else {
                jquery_element.html(gettext("No data available."));
              }
            });
          }
        },
        error: function (jqXHR, textStatus, errorThrown) {
          jquery_element.html("No data available.");
          horizon.alert("error", gettext("An error occurred. Please try again later."));
        },
        complete: function (data, textStatus, jqXHR) {
          jquery_element.spin(false);
        }
      });
    }

  },
  refresh: function(html_element, data_series){
    var chart = new this.LineChart(this, html_element)
    // FIXME save chart objects somewhere so I can use them again when
    // e.g. I am switching tabs, or if I want to update them
    // via web sockets
    // this.charts.add_or_update(chart)
    chart.refresh(data_series);
  }
}

/* init the graphs */
horizon.addInitFunction(function () {
  horizon.d3_line_chart_overview.init("div[data-chart-type='line_chart_overview']");
});
