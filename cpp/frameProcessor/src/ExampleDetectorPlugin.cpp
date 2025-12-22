/*
 * ExampleDetectorPlugin.cpp
 *
 *  Created on: 11 Nov 2025
 *      Author: gnx91527
 */

#include "ExampleDetectorPlugin.h"
#include "DebugLevelLogger.h"


#define IMAGE_WIDTH 256
#define IMAGE_HEIGHT 256

namespace FrameProcessor
{
ExampleDetectorPlugin::ExampleDetectorPlugin()
{
  // Setup logging for the class
  logger_ = Logger::getLogger("FP.ExampleDetectorPlugin");
  LOG4CXX_INFO(logger_, "ExampleDetectorPlugin version " << this->get_version_long() << " loaded");
}

ExampleDetectorPlugin::~ExampleDetectorPlugin()
{
}

/**
 * Set configuration options for the LATRD processing plugin.
 *
 * This sets up the process plugin according to the configuration IpcMessage
 * objects that are received. The options are searched for:
 * CONFIG_PROCESS - Calls the method processConfig
 *
 * \param[in] config - IpcMessage containing configuration data.
 * \param[out] reply - Response IpcMessage.
 */
void ExampleDetectorPlugin::configure(OdinData::IpcMessage& config, OdinData::IpcMessage& reply)
{
  LOG4CXX_DEBUG_LEVEL(1, logger_, config.encode());
}

void ExampleDetectorPlugin::requestConfiguration(OdinData::IpcMessage& reply)
{
}

void ExampleDetectorPlugin::status(OdinData::IpcMessage& status)
{
//  status.set_param(get_name() + "/dropped_packets", dropped_packets);
//  status.set_param(get_name() + "/invalid_packets", invalid_packets);
}

void ExampleDetectorPlugin::process_frame(boost::shared_ptr<Frame> frame)
{
  // Extract the frame header from the frame
  ExampleDetector::FrameHeader* hdr_ptr = static_cast<ExampleDetector::FrameHeader*>(frame->get_data_ptr());
  // Log details of the frame
  LOG4CXX_TRACE(logger_, "Received a new frame with number: << " << hdr_ptr->frame_number);
  LOG4CXX_DEBUG(logger_, "Frame state: " << hdr_ptr->frame_state);
  LOG4CXX_DEBUG(logger_, "Packets received: " << hdr_ptr->packets_received << " expected: " << ExampleDetector::num_packets);

  // Create and populate metadata for the output frame
  FrameMetaData frame_meta;
  frame_meta.set_dataset_name("example");
  frame_meta.set_data_type(raw_8bit);
  frame_meta.set_frame_number(static_cast<long long>(hdr_ptr->frame_number));
  dimensions_t dims(2);
  dims[0] = IMAGE_HEIGHT;
  dims[1] = IMAGE_WIDTH;
  frame_meta.set_dimensions(dims);
  frame_meta.set_compression_type(no_compression);
  // Set metadata on existing frame
  frame->set_meta_data(frame_meta);

  // Calculate output image size
  const std::size_t output_image_size = IMAGE_WIDTH * IMAGE_HEIGHT * sizeof(uint8_t);

  // Set output image size on existing frame
  frame->set_image_size(output_image_size);

  // Set iamge offset on exisitng frame
  frame->set_image_offset(sizeof(ExampleDetector::FrameHeader));

  // Push the frame to the next plugin
  this->push(frame);
}

/**
  * Get the plugin major version number.
  *
  * \return major version number as an integer
  */
int ExampleDetectorPlugin::get_version_major()
{
  return 0;
}

/**
  * Get the plugin minor version number.
  *
  * \return minor version number as an integer
  */
int ExampleDetectorPlugin::get_version_minor()
{
  return 0;
}

/**
  * Get the plugin patch version number.
  *
  * \return patch version number as an integer
  */
int ExampleDetectorPlugin::get_version_patch()
{
  return 0;
}

/**
  * Get the plugin short version (e.g. x.y.z) string.
  *
  * \return short version as a string
  */
std::string ExampleDetectorPlugin::get_version_short()
{
  return "0.0.0";
}

/**
  * Get the plugin long version (e.g. x.y.z-qualifier) string.
  *
  * \return long version as a string
  */
std::string ExampleDetectorPlugin::get_version_long()
{
  return "0.0.0";
}

} /* namespace FrameProcesser */
