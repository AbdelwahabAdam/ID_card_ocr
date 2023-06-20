from PyPDF2 import PdfReader
import textract
import cv2
import numpy as np
import os
import glob
import re
import json
import sys
import re

class ExtractFromDoc:
    def __init__(self, threshold_doc, threshold) -> None:
        self.final_output = {}
        self.output = {}
        self.threshold_doc = threshold_doc
        self.threshold = threshold
        # self.main()

    def extract_text(self, path):
        # Extract text using Textract
        text = textract.process(path, method='tesseract', language='deu')

        # Print the extracted text
        return text.decode('utf-8'),0

    def read_pdf_split_images(self):
        ## This method search for pdf file in src directory, and extract images from it.
        directory = 'src'
        print(os.listdir(os.path.join(os.curdir,directory)))
        for filename in os.listdir(os.path.join(os.curdir,directory)):
            if filename.endswith('.pdf'):
                ids =0
                reader = PdfReader(os.path.join(os.curdir,directory,filename))
                for page in reader.pages:
                    for image in page.images:
                        with open(f"res/id_{ids}.jpg", "wb") as fp:
                            fp.write(image.data)
                    ids+=1

    def clear_field_new(self, var, *field):
        val = ''.join(var)
        for i in field:
            val = val.replace(i, '')
        val = val.strip()
        return val

    def get_src_images(self):
        # print( glob.glob(os.path.join('res', "*.jpg")))
        return  glob.glob(os.path.join('res', "*.jpg"))

    def get_temp_images(self,path):
        return glob.glob(os.path.join(path,  "*.png"))

    def crop_image_and_detect_text(self):
        self.output['res'] = {}
        cropped_images = glob.glob(os.path.join(f'res','detection',  "*.png"))
        for sup_image_path in cropped_images:
            sup_image_name = sup_image_path.split('\\')[-1].replace('.png', '') ###TODO CHANGE \\ TO /
            if 'res' not in sup_image_name:
                text, confidence = self.extract_text(sup_image_path)
                self.output['res'][sup_image_name] =  {'value':text, 'confidence':0}   ##text

    def add_data_to_output(self):
        self.final_output['res'] = {}
        # print("********************************")
        # print(f'self.output: {self.output}')
        # print("********************************")
        for val in self.output['res']:
            if 'birth' in val :
                name_var = re.sub(r"[^0-9.]", "", self.output['res'][val]['value']) 
                self.final_output['res']['birth'] = {'value':name_var}

            if 'expirty' in val :
                name_var = re.sub(r"[^0-9.]", "", self.output['res'][val]['value']) 
                self.final_output['res']['expirty'] = {'value':name_var}

            if 'startDat' in val :
                name_var = re.sub(r"[^0-9.]", "", self.output['res'][val]['value']) 
                self.final_output['res']['startDat'] = {'value':name_var}

            if 'Fname' in val :
                cleaned_string = re.sub(r"[\r\n\t\x0c]", "", self.output['res'][val]['value'])
                name_var = self.clear_field_new(cleaned_string,'Name', 'Surname', 'Nom','/',',','Geburts','name','at birth','naissance').strip()
                self.final_output['res']['Fname'] = {'value':name_var}

            if 'Secname' in val :
                cleaned_string = re.sub(r"[\r\n\t\x0c]", "", self.output['res'][val]['value'])
                name_var = self.clear_field_new(cleaned_string, 'Given', 'names','/',',','Vornamen','vornamen','Prenoms','prenoms','prénom','Prénom').strip()
                if len(name_var.split(' ')) > 1:
                    name_var = name_var.split(' ')[-1]
                self.final_output['res']['Sname'] = {'value':name_var}

            if 'serialNum' in val :
                cleaned_string = re.sub(r"[\r\n\t\x0c]", "", self.output['res'][val]['value'])
                name_var = self.clear_field_new(cleaned_string, 'BUNDESREPUBLIK', 'DEUTSCHLAND','/',',','|').strip().split(' ')
                filtered_list = [item for item in name_var if len(item) > 5]
                if filtered_list:
                    self.final_output['res']['serialNum'] = {'value':filtered_list[-1]}
                else:
                    self.final_output['res']['serialNum'] = {'value':''}

    def get_output(self):
        for page in self.final_output:
            with open(f"{os.path.join('res','output.json')}", 'w', encoding='utf8') as json_file:
                json.dump(self.final_output[page],
                        json_file, ensure_ascii=False)
                print(f"Output: res/output.json")

    def detect_id_and_split(self):
        ### here
        docs_images = self.get_src_images()     ### Read src directory and get images path as list
        if not docs_images:
            print("src directory is empty")
            print("The pdf is empty!")
            print("Terminating the Script")
            sys.exit()

        # ### Create res/sup-diectories to divide src
        dir_to_creat = ['detection']
        for file in dir_to_creat:
            if not os.path.exists(os.path.join('res',file)):
                os.makedirs(os.path.join('res',file))

        ### loop on src images.
        for doc_image_path in docs_images:
            ### Remove full path and extension > /src/page1_elec.png >> page1_elec.
            name = doc_image_path.split('/')[-1].replace('.jpg', '') 
            # Read input src image using opencv.
            temp_image = cv2.imread(doc_image_path)

            # Resize input src image using opencv.
            # doc_image = cv2.resize(temp_image, (1960, 2824))
            doc_image = temp_image

            # Convert to gray scale >> because some Images as colored and to enhance detection.
            gray_doc_image = cv2.cvtColor(doc_image, cv2.COLOR_BGR2GRAY)

            # Get template Images.
            temp_images = self.get_temp_images(path='temp')

            # Add some flags to better customize the loop
            # To draw and extract the first Image found (Only exist once in the doc).
            done_Fname = False
            done_Secname = False
            done_serialNumb = False
            done_Enddate = False
            done_birth = False
            done_startDate = False
            # Loop of each template file to find matches with threshold >>> IMPORTANT
            for temp_image in temp_images:
                # Load the template image and the target image.
                template_img = cv2.imread(temp_image)
                gray_template_img = cv2.cvtColor(
                    template_img, cv2.COLOR_BGR2GRAY)
                # Get the dimensions of the template image.
                template_height, template_width = gray_template_img.shape[:2]
                # Perform template matching.
                result = cv2.matchTemplate(
                    gray_doc_image, gray_template_img, cv2.TM_CCOEFF_NORMED)
                
                # Define a threshold value to consider a match.
                temp_temp = temp_image.split('\\')[-1].split('_')[:-1][0]               ###TODO CHANGE \\ TO /
                threshold = self.threshold_doc.get(temp_temp, self.threshold)
                
                # Get the location of the matches
                locations = list(zip(*np.where(result >= threshold)))
                # Draw rectangles around the matches.
                for loc in locations:
                    top_left_corner = loc[::-1]
                    bottom_right_corner = (
                        top_left_corner[0] + template_width, top_left_corner[1] + template_height)
                    if 'Secname' in temp_image and done_Fname == False:
                            height = doc_image.shape[0]
                            width = doc_image.shape[1]
                            img = doc_image[top_left_corner[1]:bottom_right_corner[1]+40 ,
                                            top_left_corner[0]:bottom_right_corner[0]+50]

                            name = name.split('\\')[-1]
                            
                            self.write_threshold(img=img,thresh=False,img_name='Secname',name=name)
                            # cv2.imwrite(os.path.join('res','detection',f'{name}_Secname.png'), img)

                            cv2.rectangle(doc_image,
                                        (top_left_corner[0], top_left_corner[1]),
                                        (bottom_right_corner[0]+50, bottom_right_corner[1]+40), 
                                        (0, 255, 0), 2)
                            done_Fname = True
                            cv2.imwrite(os.path.join('res','detection',f'{name}_res.png'), doc_image)
                            # matching = 'done'
                            break

                    if 'Fname' in temp_image and done_Secname == False:
                            height = doc_image.shape[0]
                            width = doc_image.shape[1]
                            img = doc_image[top_left_corner[1]:bottom_right_corner[1]+50 ,
                                            top_left_corner[0]:bottom_right_corner[0]+width]

                            name = name.split('\\')[-1]

                            self.write_threshold(img=img,thresh=False,img_name='Fname',name=name)

                            # cv2.imwrite(os.path.join('res','detection',f'{name}_Fname.png'), img)
                            cv2.rectangle(doc_image,
                                        (top_left_corner[0], top_left_corner[1]),
                                        (bottom_right_corner[0]+width, bottom_right_corner[1]+50), 
                                        (0, 255, 0), 2)
                            done_Secname = True
                            cv2.imwrite(os.path.join('res','detection',f'{name}_res.png'), doc_image)
                            # matching = 'done'
                            break

                    if 'startDate' in temp_image and done_startDate == False:
                            height = doc_image.shape[0]
                            width = doc_image.shape[1]
                            img = doc_image[top_left_corner[1]:bottom_right_corner[1]+50 ,
                                            top_left_corner[0]:bottom_right_corner[0]+50]

                            name = name.split('\\')[-1]
                            self.write_threshold(img=img,thresh=False,img_name='startDat',name=name)

                            # cv2.imwrite(os.path.join('res','detection',f'{name}_startDat.png'), img)
                            cv2.rectangle(doc_image,
                                        (top_left_corner[0], top_left_corner[1]),
                                        (bottom_right_corner[0]+50, bottom_right_corner[1]+50), 
                                        (0, 255, 0), 2)
                            done_startDate = True
                            cv2.imwrite(os.path.join('res','detection',f'{name}_res.png'), doc_image)
                            # matching = 'done'
                            break

                    if 'birth' in temp_image and done_birth == False:
                            height = doc_image.shape[0]
                            width = doc_image.shape[1]
                            img = doc_image[top_left_corner[1]:bottom_right_corner[1]+50 ,
                                            top_left_corner[0]-70:bottom_right_corner[0]+25]

                            name = name.split('\\')[-1]

                            self.write_threshold(img=img,thresh=False,img_name='birth',name=name)

                            # cv2.imwrite(os.path.join('res','detection',f'{name}_birth.png'), img)
                            cv2.rectangle(doc_image,
                                        (top_left_corner[0]-70, top_left_corner[1]),
                                        (bottom_right_corner[0]+25, bottom_right_corner[1]+50), 
                                        (0, 255, 0), 2)
                            done_birth = True
                            cv2.imwrite(os.path.join('res','detection',f'{name}_res.png'), doc_image)
                            # matching = 'done'
                            break

                    if 'expirty' in temp_image and done_Enddate == False:
                            height = doc_image.shape[0]
                            width = doc_image.shape[1]
                            img = doc_image[top_left_corner[1]:bottom_right_corner[1]+40 ,
                                            top_left_corner[0]-70:bottom_right_corner[0]+25]

                            name = name.split('\\')[-1]

                            self.write_threshold(img=img,thresh=False,img_name='expirty',name=name)

                            # cv2.imwrite(os.path.join('res','detection',f'{name}_expirty.png'), img)
                            cv2.rectangle(doc_image,
                                        (top_left_corner[0]-70, top_left_corner[1]),
                                        (bottom_right_corner[0]+25, bottom_right_corner[1]+40), 
                                        (0, 255, 0), 2)
                            done_Enddate = True
                            cv2.imwrite(os.path.join('res','detection',f'{name}_res.png'), doc_image)
                            # matching = 'done'
                            break

                    if 'serialNum' in temp_image and done_serialNumb == False:
                            height = doc_image.shape[0]
                            width = doc_image.shape[1]
                            img = doc_image[top_left_corner[1]:bottom_right_corner[1]+15 ,
                                            top_left_corner[0]:int(width)]

                            name = name.split('\\')[-1]
                            self.write_threshold(img=img,thresh=True,img_name='serialNum',name=name)


                            # cv2.imwrite(os.path.join('res','detection',f'{name}_serialNum.png'), img)
                            cv2.rectangle(doc_image,
                                        (top_left_corner[0], top_left_corner[1]),
                                        (int(width), bottom_right_corner[1]+15), 
                                        (0, 255, 0), 2)
                            done_serialNumb = True
                            cv2.imwrite(os.path.join('res','detection',f'{name}_res.png'), doc_image)
                            # matching = 'done'
                            break

    def write_threshold(self,img,name,img_name,thresh):
        # Set the threshold value to 10
        threshold_value = 100

        # Set the maximum value to 255
        max_value = 255

        # Set the thresholding type to cv2.THRESH_BINARY_INV
        threshold_type = cv2.THRESH_BINARY_INV

        if thresh:
            ret, thresholded_img = cv2.threshold(img, threshold_value, max_value, threshold_type)
            cv2.imwrite(os.path.join('res','detection',f'{name}_{img_name}.png'), thresholded_img)
        else:
            cv2.imwrite(os.path.join('res','detection',f'{name}_{img_name}.png'), img)

    def main(self):
        print("Start Main")
        self.read_pdf_split_images()
        self.detect_id_and_split()
        self.crop_image_and_detect_text()
        self.add_data_to_output()
        self.get_output()
        print("End Main")


if __name__=="__main__":
    ### You have to put the temp directory next to the script.
    ### The result will be in res directory.
    ExtractFromDoc(threshold_doc={
        'birth': 0.8, 
        'expirty': 0.8, 
        'Fname': 0.8,
        'Secname': 0.8,
        'serialNum': 0.8,
        'startDate': 0.8,
    }, threshold=0.8)