/* global gettext */
/* eslint react/no-array-index-key: 0 */

import PropTypes from 'prop-types';
import React from 'react';
import ReactDOM from 'react-dom';

export function CourseOrLibraryListing(props) {
  const allowReruns = props.allowReruns;
  const linkClass = props.linkClass;
  const idBase = props.idBase;

  console.info( ( props.idBase==="course") ? "ACTIVE COURSES===" : "")
  console.info( ( props.idBase==="archived") ? "ARCHIVED COURSES===" : "")
  console.info( props );

  const templates = props.items.filter( (item)=>item.run==='Template');
  const sections = props.items.filter( (item)=>item.run!='Template');

  console.info('templates:', templates);
  console.info('sections:', sections);

  function getBookCard( course_number ){
    switch( course_number ){
      case "978-1-947172-00-5": // OpenStax Prealgebra
        return "https://d3bxy9euw4e147.cloudfront.net/oscms-prodcms/media/documents/prealgebra_1.svg";
      case "978-1-947172-25-8": // OpenStax Elementary Algebra
        return "https://d3bxy9euw4e147.cloudfront.net/oscms-prodcms/media/documents/elementary-algebra.svg";
      case "978-1-947172-26-5": // OpenStax Intermediate Algebra
        return "https://d3bxy9euw4e147.cloudfront.net/oscms-prodcms/media/documents/intermediate-algebra.svg";
      case "978-1-947172-10-4": // OpenStax Algebra and Trigonometry
        return "https://d3bxy9euw4e147.cloudfront.net/oscms-prodcms/media/documents/algebra_trigonometry.svg";
      case "978-1-947172-12-8": // OpenStax College Algebra
        return "https://d3bxy9euw4e147.cloudfront.net/oscms-prodcms/media/documents/college_algebra.svg";
      case "978-1-947172-06-7": // OpenStax Precalculus
        return "https://d3bxy9euw4e147.cloudfront.net/oscms-prodcms/media/documents/precalculus.svg";
      case "978-1-947172-13-5": // OpenStax Calculus Volume 1
        return "https://d3bxy9euw4e147.cloudfront.net/oscms-prodcms/media/documents/calculus-v1.svg";
      case "978-1-947172-14-2": // OpenStax Calculus Volume 2
        return "https://d3bxy9euw4e147.cloudfront.net/oscms-prodcms/media/documents/calculus-v2.svg";
      case "978-1-947172-16-6": // OpenStax Calculus Volume 3
        return "https://d3bxy9euw4e147.cloudfront.net/oscms-prodcms/media/documents/calculus-v3.svg";
      case "978-1-947172-05-0": // OpenStax Introductory Statistics
        return "https://d3bxy9euw4e147.cloudfront.net/oscms-prodcms/media/documents/statistics.svg";
      case "978-1-947172-47-0": // OpenStax Introductory Business Statistics
        return "https://d3bxy9euw4e147.cloudfront.net/oscms-prodcms/media/documents/IntroductoryBusinessStatistics-bookcard.svg";
      default:
        return "https://avatars2.githubusercontent.com/u/3805549?s=400&v=4"
      }
  }

  let templateList = (      
    <ul className="list-courses list-templates">
    {
      templates.map((item, i) =>
        (
          <li key={i} className="course-item template-item" data-course-key={item.course_key}>
            <a className={"book-block " + linkClass} href={item.rerun_link} alt={"Create new " + item.display_name}>
              <img src={getBookCard(item.number)} alt={item.display_name}></img>
              <h3 className="course-title" id={`title-${idBase}-${i}`}>{item.display_name}</h3>
              <div className="course-metadata rover-template">
                <span className="course-org metadata-item">
                  <span className="label">{gettext('Organization:')}</span>
                  <span className="value">{item.org}</span>
                </span>
                { item.run &&
                <span className="course-run metadata-item">
                  <span className="label">{gettext('Course Run:')}</span>
                  <span className="value">{item.run}</span>
                </span>
                }
                { item.can_edit === false &&
                <span className="extra-metadata">{gettext('(Read-only)')}</span>
                }
              </div>
            </a>
            { allowReruns && item.lms_link && item.rerun_link &&
            <ul className="item-actions course-actions">
              <li className="action action-edit">
                <a
                  href={item.url}
                  rel="external"
                  className="button view-button"
                  aria-labelledby={`view-live-${idBase}-${i} title-${idBase}-${i}`}
                  id={`view-live-${idBase}-${i}`}
                >{gettext('Edit Template')}</a>
              </li>
            </ul>
            }
          </li>
        )
      )
    }
    </ul>
  )

  let sectionList = (      
    <ul className="list-courses">
    {
      sections.map((item, i) =>
        (
          <li key={i} className="course-item" data-course-key={item.course_key}>
            <a className={linkClass} href={item.url}>
              <h3 className="course-title" id={`title-${idBase}-${i}`}>{item.display_name}</h3>
              <div className="course-metadata custom-course-section">
                { item.run &&
                <span className="course-run metadata-item">
                  <span className="label">{gettext('Course Run:')}</span>
                  <span className="value">{item.run}</span>
                </span>
                }
                { item.can_edit === false &&
                <span className="extra-metadata">{gettext('(Read-only)')}</span>
                }
              </div>
            </a>
            { item.lms_link && item.rerun_link &&
            <ul className="item-actions course-actions">
              { allowReruns &&
              <li className="action action-rerun">
                <a
                  href={item.rerun_link}
                  className="button rerun-button"
                  aria-labelledby={`re-run-${idBase}-${i} title-${idBase}-${i}`}
                  id={`re-run-${idBase}-${i}`}
                >{gettext('Copy Course Section')}</a>
              </li>
              }
              <li className="action action-view">
                <a
                  href={item.lms_link}
                  rel="external"
                  className="button view-button"
                  aria-labelledby={`view-live-${idBase}-${i} title-${idBase}-${i}`}
                  id={`view-live-${idBase}-${i}`}
                >{gettext('Student View')}</a>
              </li>
            </ul>
            }
          </li>
        ),
      )
    }
  </ul>
  )

  if( props.idBase==="course" ){
    return (
      <div>
        {templateList}
        {props.idBase==="course" && <h2 className="my-course-sections-title">My Course Sections</h2>}
        {sectionList}
      </div>
    );
  
  }else{ // archives
    return (
      <div>
        {sectionList}
      </div>
    );  
  }
}

CourseOrLibraryListing.propTypes = {
  allowReruns: PropTypes.bool.isRequired,
  idBase: PropTypes.string.isRequired,
  items: PropTypes.arrayOf(PropTypes.object).isRequired,
  linkClass: PropTypes.string.isRequired,
};
