package org.opensha.sha.imr.attenRelImpl;

import org.opensha.commons.data.NamedObjectAPI;
import org.opensha.commons.param.event.ParameterChangeEvent;
import org.opensha.commons.param.event.ParameterChangeListener;
import org.opensha.sha.imr.AttenuationRelationship;
import org.opensha.sha.imr.ScalarIntensityMeasureRelationshipAPI;

public class BW_1997_AttenRel extends AttenuationRelationship implements
ScalarIntensityMeasureRelationshipAPI,
NamedObjectAPI, ParameterChangeListener {
	public double getMean(double magnitude, double epicentralDistance) {
		double result = 0.0;
		return result;
	} // getMean()

	@Override
	protected void initEqkRuptureParams() {
		// TODO Auto-generated method stub
		
	}

	@Override
	protected void initPropagationEffectParams() {
		// TODO Auto-generated method stub
		
	}

	@Override
	protected void initSiteParams() {
		// TODO Auto-generated method stub
		
	}

	@Override
	protected void initSupportedIntensityMeasureParams() {
		// TODO Auto-generated method stub
		
	}

	@Override
	protected void setPropagationEffectParams() {
		// TODO Auto-generated method stub
		
	}

	@Override
	public double getMean() {
		// TODO Auto-generated method stub
		return 0;
	}

	@Override
	public double getStdDev() {
		// TODO Auto-generated method stub
		return 0;
	}

	@Override
	public String getShortName() {
		// TODO Auto-generated method stub
		return null;
	}

	@Override
	public void setParamDefaults() {
		// TODO Auto-generated method stub
		
	}

	@Override
	public void parameterChange(ParameterChangeEvent event) {
		// TODO Auto-generated method stub
		
	}

} // class BW_1997_AttenRel()
