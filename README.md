# firm_web-scraping
The aim of this project is to scrape metadata of business firms given only their name and country where they are operating.

Please refer to the [Wiki](https://github.com/worldbank/Firms-Web-Scraping/wiki/General-System-Overview) for extensive documentation.

The system initally requires a training phase for its _oracles_, as illustrated below:

[[https://github.com/worldbank/Firms-Web-Scraping/blob/master/utils/examples/start_phase.png]]

Once started the oracles are trained the system can enter a general input phase, where it executes the _Go_ and _Ongoing Evaluation_ phases, as illustrated below:

!(image of the Go and Evaluation phases and their interconnection)[[https://github.com/worldbank/Firms-Web-Scraping/blob/master/utils/examples/do_evaluation_phase.png]
