# firm_web-scraping
The aim of this project is to scrape metadata of business firms given only their name and country where they are operating.

Please refer to the [Wiki](https://github.com/worldbank/Firms-Web-Scraping/wiki/General-System-Overview) for extensive documentation.

The system initally requires a training phase for its _oracles_, as illustrated below:

![Start phase](https://user-images.githubusercontent.com/8014151/27988719-28757ae4-63f7-11e7-804c-59c7008be8d6.png)

Once started the oracles are trained the system can enter a general input phase, where it executes the _Go_ and _Ongoing Evaluation_ phases, as illustrated below:

![Do and Evaluation phases](https://user-images.githubusercontent.com/8014151/27988720-2bf37f5e-63f7-11e7-97a0-290b41de41c1.png)

To collect Firm metadata the system uses a completely different process called [referral based crowdsourcing](http://journals.plos.org/plosone/article?id=10.1371/journal.pone.0045924). 

![firmmetadata](https://user-images.githubusercontent.com/8014151/28217177-38500bca-6882-11e7-9f36-b40ce7487915.png)
