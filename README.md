# This is all in one packet

I'm not familiar with JS canvas, so I decided to build up a small TkInter application to use all the things I have 
to perform the prediction. 

## Task list
- [x] Use the Idea of InvoiceNet to build the application, first I need to clone the InvoiceNet GUI
- [x] Enhance the GUI by using Nanoet GUI as template and use Tkinter Designer application
- [x] Embed the VegSeg to the segmentation process
- [x] Allow user choose fields and then segmentation on these fields
- [x] Enhance the UI by adding more tabs

* Add UI and Functional code for Camera calibration task:
  - [ ] Add UI
  - [ ] Functional Code
- [ ] Add UI and Functional code for Line tracing task 
- [ ] Add UI and Functional code for Measurement task

Result (Completed on Feb 12, 2022)
* Base on [InvoiceNet GUI](https://github.com/naiveHobo/InvoiceNet) and then do som modification with [Sun-Valley Tkinter theme](/home/hp/Pictures/Screenshot from 2022-02-11 19-22-08.png)

![](./readme_images/im1.png)

* Change the original app to Image base application instead of PDF base application.

![](./readme_images/im2.png)

* Use Pytorch model to perform segmentation

![](./readme_images/im3.png)
