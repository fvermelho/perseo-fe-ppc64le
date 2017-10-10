/*
 * Copyright 2015 Telefonica Investigación y Desarrollo, S.A.U
 *
 * This file is part of perseo-fe
 *
 * perseo-fe is free software: you can redistribute it and/or
 * modify it under the terms of the GNU Affero General Public License as
 * published by the Free Software Foundation, either version 3 of the License,
 * or (at your option) any later version.
 *
 * perseo-fe is distributed in the hope that it will be useful,
 * but WITHOUT ANY WARRANTY; without even the implied warranty of
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.
 * See the GNU Affero General Public License for more details.
 *
 * You should have received a copy of the GNU Affero General Public
 * License along with perseo-fe.
 * If not, see http://www.gnu.org/licenses/.
 *
 * For those usages not covered by the GNU Affero General Public License
 * please contact with::[contacto@tid.es]
 */
'use strict';

var util = require('util'),
    uuid = require('uuid'),
    async = require('async'),
    config = require('../../config'),
    constants = require('../constants'),
    myutils = require('../myutils'),
    alarm = require('../alarm'),
    UtmConverter = require('utm-converter'),
    converter = new UtmConverter(),
    errors = {};

function parseLocation(locStr) {
    var position,
        lat,
        lon,
        utmResult;

    position = locStr.split(',', 3);
    if (position.length !== 2) {
        return new errors.InvalidLocation(position);
    }
    lat = parseFloat(position[0]);
    if (isNaN(lat) || !isFinite(lat)) {
        return new errors.InvalidLatitude(lat);
    }
    lon = parseFloat(position[1]);
    if (isNaN(lon) || !isFinite(lon)) {
        return new errors.InvalidLongitude(lon);
    }
    utmResult = converter.toUtm({coord: [lon, lat]}); // CAUTION: Longitude first element

    return {
        lat: lat,
        lon: lon,
        x: utmResult.coord.x,
        y: utmResult.coord.y
    };
}

// http://www.ecma-international.org/ecma-262/5.1/#sec-15.9.1.15
function parseDate(isoStr) {
    var date,
        ts,
        error;

    ts = Date.parse(isoStr);
    if (isNaN(ts)) {
        error = new errors.InvalidDateTime(isoStr);
        myutils.logErrorIf(error);
        return error;
    } else {
        date = new Date(isoStr);
        return {
            ts: ts,
            day: date.getDate(),
            month: date.getMonth() + 1,
            year: date.getFullYear(),
            hour: date.getHours(),
            minute: date.getMinutes(),
            second: date.getSeconds(),
            millisecond: date.getMilliseconds(),
            dayUTC: date.getUTCDate(),
            monthUTC: date.getUTCMonth() + 1,
            yearUTC: date.getUTCFullYear(),
            hourUTC: date.getUTCHours(),
            minuteUTC: date.getUTCMinutes(),
            secondUTC: date.getUTCSeconds(),
            millisecondUTC: date.getUTCMilliseconds()
        };
    }
}

function addTimeInfo(object, key, timeInfo) {
    if (timeInfo && !(timeInfo instanceof Error)) {
        for (var p in timeInfo) {
            if (timeInfo.hasOwnProperty(p)) {
                object[key + '__' + p] = timeInfo[p];
            }
        }
    }
}

function processCBNotice(service, subservice, ncr, ix) {
    var n = {},
        pp,
        temp,
        location = null,
        timeInfo = null,
        localError = null;

    n.noticeId = uuid.v1();
    n.noticeTS = Date.now();

    try {
        n.id = ncr.contextResponses[ix].contextElement.id;
        n.type = ncr.contextResponses[ix].contextElement.type;
        n.isPattern = ncr.contextResponses[ix].contextElement.isPattern;
        n.subservice = subservice;
        n.service = service;
        n.subscriptionId = ncr.subscriptionId;

        localError = null;
        //Transform name-value-type
        ncr.contextResponses[ix].contextElement.attributes.forEach(function(attr) {
            if (attr.name === 'id') {
                localError = new errors.IdAsAttribute(JSON.stringify(attr));
            } else if (attr.name === 'type') {
                localError = new errors.TypeAsAttribute(JSON.stringify(attr));
            }
            else {
                n[attr.name] = attr.value;
                n[attr.name + '__type'] = attr.type;

                // NGSIv1 location attribute (only one should be present)
                // see links in issues/198
                if (attr.type === 'geo:point') {
                    location = parseLocation(attr.value);
                }

                if (attr.name === 'TimeInstant' ||
                    attr.type === 'urn:x-ogc:def:trs:IDAS:1.0:ISO8601' ||
                    attr.type === 'DateTime') {
                    timeInfo = parseDate(attr.value);
                    addTimeInfo(n, attr.name, timeInfo);
                }

                if (attr.metadatas) {
                    for (var i = 0; i < attr.metadatas.length; i++) {
                        n[attr.name + '__metadata__' + attr.metadatas[i].name] = attr.metadatas[i].value;
                        n[attr.name + '__metadata__' + attr.metadatas[i].name + '__type'] = attr.metadatas[i].type;

                        if (attr.metadatas[i].name === 'TimeInstant' ||
                            attr.metadatas[i].type === 'urn:x-ogc:def:trs:IDAS:1.0:ISO8601' ||
                            attr.metadatas[i].type === 'DateTime') {
                            timeInfo = parseDate(attr.metadatas[i].value);
                            addTimeInfo(n, attr.name + '__metadata__' + attr.metadatas[i].name, timeInfo);
                        }

                        // Deprecated location in NGSV1
                        // see links in issues/198
                        if (attr.metadatas[i].name === 'location') {
                            location = parseLocation(attr.value);
                        }
                    }
                }
                if (location !== null) {
                    if (location instanceof Error) {
                        localError = location;
                    }
                    else {
                        n[attr.name + '__lat'] = location.lat;
                        n[attr.name + '__lon'] = location.lon;
                        n[attr.name + '__x'] = location.x;
                        n[attr.name + '__y'] = location.y;

                    }
                }
            }
        });
        if (localError !== null) {
            return localError;
        }

        Object.keys(n).forEach(function(p) {
            //Change dots in key to double-underscore as in rules to avoid confusing EPL engine
            pp = p.replace(/\./g, '__');
            temp = n[p];
            delete n[p];
            n[pp] = temp;
        });

        n = myutils.flattenMap('', n);

    } catch (ex) { // SHOULD BE ex instanceof TypeError. Do not do anything else inside try
        localError = new errors.InvalidNotice(JSON.stringify(ncr));
        myutils.logErrorIf(localError);
        return localError;
    }
    return n;
}


function processCBNoticev2(service, subservice, ncr, ix) {
    var n = {},
        pp,
        temp,
        location = null,
        timeInfo = null,
        localError = null;

    n.noticeId = uuid.v1();
    n.noticeTS = Date.now();

    try {
        n.id = ncr.data[ix].id;
        n.type = ncr.data[ix].type;
        // n.isPattern = undefined;
        n.subservice = subservice;
        n.service = service;
        n.subscriptionId = ncr.subscriptionId;

        localError = null;
        //Transform name-value-type

        Object.keys(ncr.data[ix]).forEach(function(key, index) {
          var attrName = key;
          var attr = ncr.data[ix][attrName];
          var attrType = attr.type;
          var attrValue = attr.value;

          if ((key === 'id') || (key === 'type')) {
            n[key] = attr;
            n[key + '__type'] = 'string';
            return;
          }

          n[key] = attrValue;
          n[key + '__type'] = attrType;

          if (attrName === 'TimeInstant' ||
              attrType === 'urn:x-ogc:def:trs:IDAS:1.0:ISO8601' ||
              attrType === 'DateTime') {
              timeInfo = parseDate(attr.value);
              addTimeInfo(n, attrName, timeInfo);
          }
          if (attr.metadata) {
            Object.keys(attr.metadata).forEach(function(key, index) {
              var metadataName = key;
              var metadata = attr.metadata[key];

              n[attrName + '__metadata__' + metadataName] = metadata.value;
              n[attrName + '__metadata__' + metadataName + '__type'] = metadata.type;

              if (metadataName === 'TimeInstant' ||
                  metadata.type === 'urn:x-ogc:def:trs:IDAS:1.0:ISO8601' ||
                  metadata.type === 'DateTime') {
                  timeInfo = parseDate(metadata.value);
                  addTimeInfo(n, attrName + '__metadata__' + metadataName, timeInfo);
              }

              // Deprecated location in NGSV1
              // see links in issues/198
              if (metadataName === 'location') {
                  location = parseLocation(metadata.value);
              }
            });

            }
        });

        if (localError !== null) {
            return localError;
        }

        Object.keys(n).forEach(function(p) {
            //Change dots in key to double-underscore as in rules to avoid confusing EPL engine
            pp = p.replace(/\./g, '__');
            temp = n[p];
            delete n[p];
            n[pp] = temp;
        });

        n = myutils.flattenMap('', n);

    } catch (ex) { // SHOULD BE ex instanceof TypeError. Do not do anything else inside try
        localError = new errors.InvalidNotice(JSON.stringify(ncr));
        myutils.logErrorIf(localError);
        return localError;
    }
    return n;
}

function DoNotice(version, orionN, callback) {
    var notices = [],
        noticesErr = [],
        dataArr = [],
        notice,
        sps;


    // ServicePath may be a comma-separated list of servicePath
    // when an initial notification for a just created subscription
    // is created
    sps = orionN.subservice.split(',');
    if (version === 'v1') {
      if (!util.isArray(orionN.contextResponses)) {
          return callback(
              new errors.ContextResponsesNotArray('(' + typeof(orionN.contextResponses) + ')')
          );
      }
      if (orionN.contextResponses.length !== sps.length) {
          return callback(
              new errors.ServipathCountMismatch('(' + sps.length + ',' + orionN.contextResponses.length + ')')
          );
      }
    }
    for (var j = 0; j < sps.length; j++) {
        switch (version) {
          case 'v1':
            notice = processCBNotice(orionN.service, sps[j].trim(), orionN, j);
            break;
          case 'v2':
            notice = processCBNoticev2(orionN.service, sps[j].trim(), orionN, j);
            break;
        }

        if (notice instanceof Error) {
            myutils.logErrorIf(notice);
            noticesErr.push(notice);
        }
        else {
            notices.push(notice);
        }
    }
    async.each(notices, function(notice, cbEach) {
            var h = {};
            h[constants.SUBSERVICE_HEADER] = notice.subservice;
            myutils.requestHelperWOMetrics('post', {
                        url: config.perseoCore.noticesURL,
                        json: notice,
                        headers: h
                    },
                function(err, data) {
                    if (err) {
                        alarm.raise(alarm.POST_EVENT);
                        noticesErr.push(err);
                    } else {
                        alarm.release(alarm.POST_EVENT);
                        dataArr.push(data);
                    }
                    // Don't wait propagation to next core to finish, asynchronously ...
                    if (config.nextCore && config.nextCore.noticesURL) {
                        myutils.requestHelperWOMetrics('post', {
                            url: config.nextCore.noticesURL,
                            json: notice,
                            headers: h
                        }, myutils.logErrorIf);
                    }
                    cbEach();
                });
        },
        function endEach() {
            var msgArr = [], statusCode = 400;
            if (noticesErr.length === 0) { // No error happened
                return callback(null, dataArr); // signal no error to callback function
            }
            noticesErr.forEach(function(e) {
                msgArr.push(e.message);
                if (e.httpCode === 500) {
                    statusCode = 500;
                }
            });
            return callback({httpCode: statusCode, message: msgArr});
        }
    );
}

module.exports.Do = DoNotice;
module.exports.ParseLocation = parseLocation;
module.exports.ProcessCBNotice = processCBNotice;
module.exports.processCBNoticev2 = processCBNoticev2;
/**
 * Constructors for possible errors from this module
 *
 * @type {Object}
 */
module.exports.errors = errors;

(function() {
    errors.InvalidNotice = function InvalidNotice(msg) {
        this.name = 'INVALID_NOTICE';
        this.message = 'invalid notice format ' + msg;
        this.httpCode = 400;
    };
    errors.IdAsAttribute = function IdAsAttribute(msg) {
        this.name = 'ID_ATTRIBUTE';
        this.message = 'id as attribute ' + msg;
        this.httpCode = 400;
    };
    errors.TypeAsAttribute = function TypeAsAttribute(msg) {
        this.name = 'TYPE_ATTRIBUTE';
        this.message = 'type as attribute ' + msg;
        this.httpCode = 400;
    };
    errors.InvalidLocation = function InvalidLocation(msg) {
        this.name = 'INVALID_LOCATION';
        this.message = 'invalid location ' + msg;
        this.httpCode = 400;
    };
    errors.InvalidLongitude = function InvalidLongitude(msg) {
        this.name = 'INVALID_LONGITUDE';
        this.message = 'longitude is not valid ' + msg;
        this.httpCode = 400;
    };
    errors.InvalidLatitude = function InvalidLatitude(msg) {
        this.name = 'INVALID_LATITUDE';
        this.message = 'latitude is not valid ' + msg;
        this.httpCode = 400;
    };
    errors.InvalidDateTime = function InvalidDateTime(msg) {
        this.name = 'INVALID_DATETIME';
        this.message = 'datetime is not valid ' + msg;
        this.httpCode = 400;
    };
    errors.ContextResponsesNotArray = function ContextResponsesNotArray(msg) {
        this.name = 'CONTEXT_RESP_NOT_ARR';
        this.message = 'ContextResponses is not an array ' + msg;
        this.httpCode = 400;
    };
    errors.ServipathCountMismatch = function ServipathCountMismatch(msg) {
        this.name = 'CONTEXT_RESP_NOT_ARR';
        this.message = 'Number of servicepath items does not match ContextResponses' + msg;
        this.httpCode = 400;
    };
    Object.keys(errors).forEach(function(element) {
        util.inherits(errors[element], Error);
    });
})();
